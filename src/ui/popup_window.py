"""
Popup Window - ポップアップ表示システム

ダブルコピー検出時の翻訳結果ポップアップとステータス表示
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.translation_manager import TranslationManager, TranslationStatus, TranslationResult
from core.clipboard_manager import ClipboardManager
from data.language import LanguageManager
from utils.display_manager import DisplayManager


class PopupState(Enum):
    """ポップアップの状態"""
    HIDDEN = "hidden"
    STATUS_DISPLAY = "status_display"
    TRANSLATION_DISPLAY = "translation_display"
    ERROR_DISPLAY = "error_display"


@dataclass
class PopupConfig:
    """ポップアップ設定"""
    # ウィンドウ設定
    width: int = 500
    height: int = 700
    min_width: int = 400
    min_height: int = 250

    # タイムアウト設定
    status_timeout: float = 3.0  # ステータス表示タイムアウト
    auto_close_delay: float = 10.0  # 自動閉じる遅延

    # 位置設定
    offset_x: int = 50
    offset_y: int = 50

    # アニメーション設定
    fade_duration: float = 0.3
    slide_duration: float = 0.2


class PopupWindow:
    """翻訳結果ポップアップウィンドウクラス"""

    def __init__(self, config_manager, language_manager: LanguageManager):
        """
        ポップアップウィンドウの初期化

        Args:
            config_manager: 設定管理オブジェクト
            language_manager: 言語管理オブジェクト
        """
        self.config_manager = config_manager
        self.language_manager = language_manager

        # 翻訳・クリップボード管理
        self.translation_manager = TranslationManager()
        self.clipboard_manager = ClipboardManager()

        # ディスプレイ管理
        self.display_manager = DisplayManager()

        # ポップアップ状態
        self.state = PopupState.HIDDEN
        self.window: Optional[tk.Toplevel] = None
        self.root: Optional[tk.Tk] = None  # メインウィンドウへの参照
        self.current_translation_result: Optional[TranslationResult] = None

        # デバッグ用の色表示ON/OFF制御（FalseでOFF）
        self.debug_colors_enabled = False

        # 設定
        self.config = PopupConfig()

        # スレッド管理
        self._status_thread: Optional[threading.Thread] = None
        self._auto_close_thread: Optional[threading.Thread] = None
        self._stop_events = {
            'status': threading.Event(),
            'auto_close': threading.Event()
        }

        # コールバック
        self._on_translation_complete: Optional[Callable] = None
        self._on_popup_closed: Optional[Callable] = None

        print("ポップアップウィンドウ初期化完了")

    def _get_debug_color(self, debug_color: str, normal_color: str = "#f8f9fa") -> str:
        """デバッグ色の取得"""
        return debug_color if self.debug_colors_enabled else normal_color

    def set_root(self, root: tk.Tk):
        """
        メインウィンドウの参照を設定

        Args:
            root: メインウィンドウのTkオブジェクト
        """
        self.root = root

    def set_callbacks(self,
                     on_translation_complete: Optional[Callable] = None,
                     on_popup_closed: Optional[Callable] = None):
        """
        コールバック関数の設定

        Args:
            on_translation_complete: 翻訳完了時のコールバック
            on_popup_closed: ポップアップ閉じる時のコールバック
        """
        self._on_translation_complete = on_translation_complete
        self._on_popup_closed = on_popup_closed

    def show_status_popup(self, message: str = "翻訳中...", timeout: Optional[float] = None):
        """
        ステータス表示ポップアップを表示

        Args:
            message: 表示するメッセージ
            timeout: タイムアウト時間（Noneの場合はデフォルト値を使用）
        """
        if self.state != PopupState.HIDDEN:
            self._update_status_message(message)
            return

        try:
            self.state = PopupState.STATUS_DISPLAY
            self._create_popup_window()
            self._setup_status_display(message)
            self._position_window()
            self._show_window()

            # タイムアウト処理
            timeout_duration = timeout or self.config.status_timeout
            self._start_status_timeout(timeout_duration)

            print(f"ステータスポップアップ表示: {message}")

        except Exception as e:
            print(f"ステータスポップアップ表示エラー: {e}")
            self._handle_error(f"ポップアップ表示エラー: {e}")

    def show_translation_popup(self, result: TranslationResult):
        """
        翻訳結果ポップアップを表示

        Args:
            result: 翻訳結果
        """
        try:
            self.current_translation_result = result

            if self.state == PopupState.HIDDEN:
                # 新規表示
                self.state = PopupState.TRANSLATION_DISPLAY
                self._create_popup_window()
                self._setup_translation_display(result)
                self._position_window()
                self._show_window()
            else:
                # 既存ポップアップを更新（マウス位置に移動）
                self.state = PopupState.TRANSLATION_DISPLAY
                self._update_translation_display(result)
                self._position_window()  # マウス位置に移動
                self._show_window()  # フォーカスを当てる

            # 自動閉じるタイマーは開始しない（ユーザーが手動で閉じるまで表示し続ける）
            # self._start_auto_close_timer()

            # 翻訳完了コールバック
            if self._on_translation_complete:
                self._on_translation_complete(result)

            print(f"翻訳結果ポップアップ表示: {result.translated_text[:50]}...")
            print("デバッグ情報を表示するには、ターミナルで「a」を入力してください")

            # ターミナルでの入力待機（バックグラウンドで実行）
            import threading
            threading.Thread(target=self._wait_for_debug_input, daemon=True).start()

        except Exception as e:
            print(f"翻訳結果ポップアップ表示エラー: {e}")
            self._handle_error(f"翻訳結果表示エラー: {e}")

    def show_error_popup(self, error_message: str):
        """
        エラー表示ポップアップを表示

        Args:
            error_message: エラーメッセージ
        """
        try:
            self.state = PopupState.ERROR_DISPLAY
            self._create_popup_window()
            self._setup_error_display(error_message)
            self._position_window()
            self._show_window()

            # 自動閉じるタイマー開始
            self._start_auto_close_timer()

            print(f"エラーポップアップ表示: {error_message}")

        except Exception as e:
            print(f"エラーポップアップ表示エラー: {e}")

    def hide_popup(self):
        """ポップアップを非表示にする"""
        try:
            if self.window and self.window.winfo_exists():
                self.window.withdraw()
                self.window.destroy()

            self.window = None
            self.state = PopupState.HIDDEN

            # スレッド停止
            self._stop_all_threads()

            # コールバック実行
            if self._on_popup_closed:
                self._on_popup_closed()

            print("ポップアップを非表示にしました")

        except Exception as e:
            print(f"ポップアップ非表示エラー: {e}")

    def _create_popup_window(self):
        """ポップアップウィンドウを作成"""
        if self.window and self.window.winfo_exists():
            self.window.destroy()

        self.window = tk.Toplevel()
        self.window.title("CCTranslation")
        self.window.geometry(f"{self.config.width}x{self.config.height}")
        self.window.minsize(self.config.min_width, 1)  # 高さの最小制限を無効化


        # ウィンドウの設定
        self.window.transient()  # 親ウィンドウに対する子ウィンドウとして設定
        self.window.grab_set()   # モーダルウィンドウとして設定
        self.window.resizable(True, True)

        # ウィンドウプロトコル設定
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # デバッグ表示はターミナルで「a」入力で実行

        # エスケープキーでウィンドウを閉じる機能を追加
        self.window.bind('<Escape>', lambda event: self.hide_popup())

        # ウィンドウリサイズ時のレイアウト調整
        self.window.bind('<Configure>', self._on_window_resize)

        # スタイル設定
        self.window.configure(bg=self._get_debug_color("blue", "#f8f9fa"))

        # フォント設定
        self.default_font = ("Noto Sans JP", 10)
        self.title_font = ("Noto Sans JP", 12, "bold")
        self.source_font = ("Noto Sans JP", 9)
        self.result_font = ("Noto Sans JP", 10)

    def _setup_status_display(self, message: str):
        """ステータス表示の設定"""
        # メインフレーム
        main_frame = tk.Frame(self.window, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # アイコン表示（簡易版）
        icon_label = tk.Label(
            main_frame,
            text="🔄",
            font=("Arial", 24),
            bg="#f8f9fa",
            fg="#007bff"
        )
        icon_label.pack(pady=(0, 10))

        # ステータスメッセージ
        status_label = tk.Label(
            main_frame,
            text=message,
            font=self.title_font,
            bg="#f8f9fa",
            fg="#333333",
            wraplength=self.config.width - 40
        )
        status_label.pack(pady=(0, 20))

        # プログレスバー（簡易版）
        progress_frame = tk.Frame(main_frame, bg="#f8f9fa")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=self.config.width - 80
        )
        progress_bar.pack()
        progress_bar.start(10)

        # キャンセルボタン
        cancel_button = tk.Button(
            main_frame,
            text="キャンセル",
            font=self.default_font,
            command=self.hide_popup,
            bg="#dc3545",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        cancel_button.pack(pady=(20, 0))

    def _setup_translation_display(self, result: TranslationResult):
        """翻訳結果表示の設定"""
        # 分割バー廃止：source_frameとresult_frameを直接配置
        # ボタンエリアの高さ（約60px）を考慮してフレームの高さを動的に計算
        def calculate_frame_height():
            window_height = self.window.winfo_height()
            # 初期設定時は固定値を使用（button_frameはまだ作成されていない）
            button_frame_height = 35  # デフォルト値
            # パディング・余白（40px）+ 安全マージン（20px）= 60px
            padding_and_margin = 60
            available_height = max(100, window_height - button_frame_height - padding_and_margin)
            # 高さ均等化：半分ずつ
            frame_height = available_height // 2
            return frame_height

        # ボタンフレームを最初に作成（最下部に固定）
        button_frame = tk.Frame(self.window, bg=self._get_debug_color("red", "#f8f9fa"))
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20)
        button_frame.pack_propagate(False)  # 子ウィジェットのサイズに依存しない

        # 翻訳元テキスト（展開/縮小可能）
        source_frame = tk.Frame(self.window, bg=self._get_debug_color("green", "#f8f9fa"), relief=tk.FLAT)
        source_frame.pack(fill=tk.X, padx=20, pady=(5, 0))
        source_frame.pack_propagate(False)  # 子ウィジェットのサイズに依存しない

        # 原文ヘッダー（クリック可能）
        source_header = tk.Frame(source_frame, bg="#f8f9fa", height=35, relief=tk.FLAT)
        source_header.pack(fill=tk.X, padx=10, pady=(8, 0))
        source_header.pack_propagate(False)

        # 展開/縮小状態を管理（クラス変数として保存）
        self.source_expanded = tk.BooleanVar(value=True)  # デフォルトは展開状態
        source_expanded = self.source_expanded  # ローカル変数としても使用


        # ヘッダーラベル（クリック可能）
        source_label = tk.Label(
            source_header,
            text=f"▼ 原文 ({result.source_language})",
            font=self.default_font,
            bg="#f8f9fa",
            fg="#666666",
            cursor="hand2",
            anchor="w"
        )
        source_label.pack(side=tk.LEFT, fill=tk.X, expand=True)


        # クリックイベントをバインド
        def toggle_source_expansion():
            if source_expanded.get():
                # 縮小状態に切り替え
                source_expanded.set(False)
                source_label.config(text=f"▶ 原文 ({result.source_language})")
                source_text_frame.pack_forget()  # テキストボックス部分全体を非表示
                # 原文フレームの高さをヘッダーのみの高さに設定（スペースを完全に除去）
                source_frame.configure(height=35)
                # デバッグ表示は削除

                # 分割バー廃止：フレーム高さを直接制御
                # 縮小時はsource_frameを最小高さに設定
                source_frame.configure(height=35)

                # result_frameの高さを調整（利用可能な全スペースを使用）
                window_height = self.window.winfo_height()
                button_frame_height = 35  # デフォルト値
                padding_and_margin = 60
                available_height = max(100, window_height - button_frame_height - padding_and_margin)
                result_frame.configure(height=available_height - 35)
                # print(f"[DEBUG] 縮小時: source=35px, result={available_height - 35}px")  # 軽量化のためコメントアウト
            else:
                # 展開状態に切り替え
                source_expanded.set(True)
                source_label.config(text=f"▼ 原文 ({result.source_language})")
                source_text_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 8))  # テキストボックス部分を表示
                # 高さ制限を解除（動的計算値を使用）
                import tkinter.font as tkfont
                font_metrics = tkfont.Font(font=self.default_font)
                dynamic_height = font_metrics.metrics('linespace') + 8  # 動的計算による1行分
                source_frame.configure(height=dynamic_height)
                # デバッグ表示は削除

                # 分割バー廃止：フレーム高さを直接制御
                # 展開時は均等高さに設定
                window_height = self.window.winfo_height()
                button_frame_height = 35  # デフォルト値
                padding_and_margin = 60
                available_height = max(100, window_height - button_frame_height - padding_and_margin)
                frame_height = available_height // 2
                source_frame.configure(height=frame_height)
                result_frame.configure(height=frame_height)
                # print(f"[DEBUG] 展開時（高さ均等化）: source={frame_height}px, result={frame_height}px")  # 軽量化のためコメントアウト


        source_label.bind("<Button-1>", lambda e: toggle_source_expansion())
        source_header.bind("<Button-1>", lambda e: toggle_source_expansion())

        # 原文テキストエリア（境界線付き）
        source_text_frame = tk.Frame(source_frame, bg="#ffffff", relief=tk.SUNKEN, bd=1)
        source_text_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 8), expand=True)

        source_text = scrolledtext.ScrolledText(
            source_text_frame,
            wrap=tk.WORD,
            font=self.source_font,
            bg="#ffffff",
            fg="#333333",
            relief=tk.FLAT,
            borderwidth=0
        )
        source_text.pack(fill=tk.BOTH, padx=5, pady=5)
        source_text.insert("1.0", result.source_text)
        source_text.config(state=tk.DISABLED)

        # 翻訳結果
        result_frame = tk.Frame(self.window, bg=self._get_debug_color("yellow", "#f8f9fa"), relief=tk.FLAT)
        result_frame.pack(fill=tk.X, padx=20, pady=(0, 0))

        # 翻訳結果ヘッダー
        result_header = tk.Frame(result_frame, bg="#f8f9fa", height=35, relief=tk.FLAT)
        result_header.pack(fill=tk.X, padx=10, pady=(8, 0))
        result_header.pack_propagate(False)

        result_label = tk.Label(
            result_header,
            text=f"翻訳結果 ({result.target_language})",
            font=self.default_font,
            bg="#f8f9fa",
            fg="#666666",
            anchor="w"
        )
        result_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 翻訳結果テキストエリア（境界線付き）
        result_text_frame = tk.Frame(result_frame, bg="#ffffff", relief=tk.SUNKEN, bd=1)
        result_text_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 8), expand=True)

        result_text = scrolledtext.ScrolledText(
            result_text_frame,
            wrap=tk.WORD,
            font=self.result_font,
            bg="#ffffff",
            fg="#333333",
            relief=tk.FLAT,
            borderwidth=0
        )
        result_text.pack(fill=tk.BOTH, padx=5, pady=5)
        result_text.insert("1.0", result.translated_text)

        # 翻訳結果テキストエリアを編集不可にする（選択とコピーは可能）
        result_text.config(state=tk.DISABLED)

        # PanedWindowにパネルを追加
        # 分割バー廃止：フレームの高さを直接設定
        # フォントメトリクスを動的に取得して1行分の高さを計算
        import tkinter.font as tkfont
        font_metrics = tkfont.Font(font=self.default_font)
        line_height = font_metrics.metrics('linespace') + 8  # 8pxの安全マージン
        print(f"[DEBUG] フォントメトリクス: {self.default_font}, linespace={font_metrics.metrics('linespace')}px, 計算後={line_height}px")

        # 初期フレーム高さを設定（高さ均等化）
        initial_frame_height = calculate_frame_height()
        source_frame.configure(height=initial_frame_height)
        result_frame.configure(height=initial_frame_height)
        print(f"[DEBUG] 初期フレーム高さ設定: {initial_frame_height}px")

        # ボタンフレームは既に作成済み

        # コピーボタン（中央配置、最小サイズ）
        copy_button = tk.Button(
            button_frame,
            text="結果をコピー",
            font=self.default_font,  # 10ptに戻す
            command=lambda: self._copy_result(result.translated_text),
            bg=self._get_debug_color("orange", "#007bff"),
            fg="white",
            activebackground=self._get_debug_color("darkorange", "#0056b3"),
            activeforeground="white",
            relief=tk.SOLID,
            borderwidth=1,  # 枠線を1pxに削減
            highlightcolor=self._get_debug_color("green", "#007bff"),
            highlightthickness=1,  # ハイライト枠線を1pxに削減
            padx=2,  # 左右パディングを最小限に削減
            pady=1   # 上下パディングを最小限に削減
        )
        copy_button.pack(expand=True)  # 中央配置（requirements.md仕様）

        # ボタンの高さを取得してframeの高さを動的に設定
        def adjust_button_frame_height():
            """ボタンフレームの高さを動的に調整し、PanedWindowの高さも再計算"""
            try:
                copy_button.update_idletasks()  # ボタンの描画を完了させる
                button_height = copy_button.winfo_reqheight()  # ボタンの要求高さを取得
                frame_height = button_height + 6  # ボタン高さ + 6px
                button_frame.configure(height=frame_height)
                print(f"[DEBUG] ボタン高さ: {button_height}px, Frame高さ: {frame_height}px")

                # PanedWindowの高さを再計算
                window_height = self.window.winfo_height()
                button_frame_height = button_frame.winfo_reqheight()
                padding_and_margin = 60
                available_height = max(100, window_height - button_frame_height - padding_and_margin)
                paned_window.configure(height=available_height)

                # 分割バーの位置も再調整
                center_pos = available_height // 2
                paned_window.sash_place(0, 0, center_pos)
                print(f"[DEBUG] PanedWindow高さ再計算: {available_height}px, 分割バー位置: {center_pos}px")

                # デバッグ表示はCtrl+Dで手動実行

            except Exception as e:
                print(f"[DEBUG] ボタン高さ取得エラー: {e}")

        # ボタンが描画された後に高さを調整
        button_frame.after(100, adjust_button_frame_height)

    def _debug_frame_heights(self, paned_window, source_frame, result_frame, button_frame):
        """各frameの高さをデバッグ表示"""
        try:
            print("=" * 60)

            # PanedWindow
            paned_height = paned_window.winfo_height()
            paned_req_height = paned_window.winfo_reqheight()
            print(f"paned_window: {paned_req_height}px → {paned_height}px")

            # SourceFrame
            if source_frame and hasattr(source_frame, 'winfo_height'):
                source_height = source_frame.winfo_height()
                source_req_height = source_frame.winfo_reqheight()
                print(f"source_frame: {source_req_height}px → {source_height}px")

                # SourceHeader
                try:
                    for child in source_frame.winfo_children():
                        if isinstance(child, tk.Frame) and child.winfo_height() == 35:  # ヘッダーは35px固定
                            header_height = child.winfo_height()
                            header_req_height = child.winfo_reqheight()
                            print(f"source_header: {header_req_height}px → {header_height}px")
                            break
                except:
                    print(f"source_header: 取得エラー")

                # SourceTextFrame
                try:
                    for child in source_frame.winfo_children():
                        if isinstance(child, tk.Frame) and child.winfo_height() != 35:  # ヘッダー以外のフレーム
                            text_frame_height = child.winfo_height()
                            text_frame_req_height = child.winfo_reqheight()
                            print(f"source_text_frame: {text_frame_req_height}px → {text_frame_height}px")
                            break
                except:
                    print(f"source_text_frame: 取得エラー")

            # ResultFrame
            if result_frame and hasattr(result_frame, 'winfo_height'):
                result_height = result_frame.winfo_height()
                result_req_height = result_frame.winfo_reqheight()
                print(f"result_frame: {result_req_height}px → {result_height}px")

                # ResultHeader
                try:
                    for child in result_frame.winfo_children():
                        if isinstance(child, tk.Frame) and child.winfo_height() == 35:  # ヘッダーは35px固定
                            result_header_height = child.winfo_height()
                            result_header_req_height = child.winfo_reqheight()
                            print(f"result_header: {result_header_req_height}px → {result_header_height}px")
                            break
                except:
                    print(f"result_header: 取得エラー")

                # ResultTextFrame
                try:
                    for child in result_frame.winfo_children():
                        if isinstance(child, tk.Frame) and child.winfo_height() != 35:  # ヘッダー以外のフレーム
                            result_text_frame_height = child.winfo_height()
                            result_text_frame_req_height = child.winfo_reqheight()
                            print(f"result_text_frame: {result_text_frame_req_height}px → {result_text_frame_height}px")
                            break
                except:
                    print(f"result_text_frame: 取得エラー")

            # ButtonFrame
            if button_frame and hasattr(button_frame, 'winfo_height'):
                button_height = button_frame.winfo_height()
                button_req_height = button_frame.winfo_reqheight()
                print(f"button_frame: {button_req_height}px → {button_height}px")

            print("=" * 60)
        except Exception as e:
            print(f"[DEBUG] Frame高さ表示エラー: {e}")

    def _debug_frame_heights_manual(self, event=None):
        """ターミナルで「a」入力時のデバッグ表示"""
        try:
            if not self.window or not self.window.winfo_exists():
                return

            print("=" * 60)

            # 分割バー廃止：source_frameとresult_frameを直接検索
            source_frame = None
            result_frame = None
            button_frame = None

            # フレームをパック順序で検索（デバッグ色に依存しない方法）
            children = list(self.window.winfo_children())
            button_frame = None
            source_frame = None
            result_frame = None

            # button_frameは最下部（side=tk.BOTTOM）で配置されるため、最初に作成される
            # source_frameとresult_frameは順番に配置される
            frame_count = 0
            for widget in children:
                if isinstance(widget, tk.Frame):
                    if frame_count == 0:
                        button_frame = widget  # 最初のフレーム（最下部に配置）
                    elif frame_count == 1:
                        source_frame = widget  # 2番目のフレーム
                    elif frame_count == 2:
                        result_frame = widget  # 3番目のフレーム
                    frame_count += 1

            if source_frame and result_frame:
                # Window（親）
                window_height = self.window.winfo_height()
                window_req_height = self.window.winfo_reqheight()
                print(f"window: {window_req_height}px → {window_height}px")

                # 利用可能な高さの計算（paned_window相当）
                button_frame_height = 35  # デフォルト値
                if button_frame:
                    button_frame_height = button_frame.winfo_reqheight()
                padding_and_margin = 60  # padx=20*2 + pady=5 + margin=15
                available_height = max(100, window_height - button_frame_height - padding_and_margin)
                print(f"利用可能高さ（paned_window相当）: {available_height}px (window={window_height}px - button={button_frame_height}px - margin={padding_and_margin}px)")

                # 原文縮小状態
                is_collapsed = not self.source_expanded.get()
                print(f"原文縮小状態: {'縮小' if is_collapsed else '展開'}")

                # SourceFrame
                if source_frame and hasattr(source_frame, 'winfo_height'):
                    source_height = source_frame.winfo_height()
                    source_req_height = source_frame.winfo_reqheight()
                    expected_source_height = 35 if is_collapsed else available_height // 2
                    status = "✓" if source_height == expected_source_height else "✗"
                    print(f"source_frame: {source_req_height}px → {source_height}px (期待値: {expected_source_height}px) {status}")

                    # SourceHeader
                    try:
                        for child in source_frame.winfo_children():
                            if isinstance(child, tk.Frame) and child.winfo_height() == 35:  # ヘッダーは35px固定
                                header_height = child.winfo_height()
                                header_req_height = child.winfo_reqheight()
                                print(f"source_header: {header_req_height}px → {header_height}px")
                                break
                    except:
                        print(f"source_header: 取得エラー")

                    # SourceTextFrame
                    try:
                        for child in source_frame.winfo_children():
                            if isinstance(child, tk.Frame) and child.winfo_height() != 35:  # ヘッダー以外のフレーム
                                text_frame_height = child.winfo_height()
                                text_frame_req_height = child.winfo_reqheight()
                                print(f"source_text_frame: {text_frame_req_height}px → {text_frame_height}px")
                                break
                    except:
                        print(f"source_text_frame: 取得エラー")

                # ResultFrame
                if result_frame and hasattr(result_frame, 'winfo_height'):
                    result_height = result_frame.winfo_height()
                    result_req_height = result_frame.winfo_reqheight()
                    expected_result_height = available_height - 35 if is_collapsed else available_height // 2
                    status = "✓" if result_height == expected_result_height else "✗"
                    print(f"result_frame: {result_req_height}px → {result_height}px (期待値: {expected_result_height}px) {status}")

                    # ResultHeader
                    try:
                        for child in result_frame.winfo_children():
                            if isinstance(child, tk.Frame) and child.winfo_height() == 35:  # ヘッダーは35px固定
                                result_header_height = child.winfo_height()
                                result_header_req_height = child.winfo_reqheight()
                                print(f"result_header: {result_header_req_height}px → {result_header_height}px")
                                break
                    except:
                        print(f"result_header: 取得エラー")

                    # ResultTextFrame
                    try:
                        for child in result_frame.winfo_children():
                            if isinstance(child, tk.Frame) and child.winfo_height() != 35:  # ヘッダー以外のフレーム
                                result_text_frame_height = child.winfo_height()
                                result_text_frame_req_height = child.winfo_reqheight()
                                print(f"result_text_frame: {result_text_frame_req_height}px → {result_text_frame_height}px")
                                break
                    except:
                        print(f"result_text_frame: 取得エラー")

                # ButtonFrame
                if button_frame and hasattr(button_frame, 'winfo_height'):
                    button_height = button_frame.winfo_height()
                    button_req_height = button_frame.winfo_reqheight()
                    print(f"button_frame: {button_req_height}px → {button_height}px")

                    # ボタンの詳細情報
                    try:
                        copy_button = None
                        for child in button_frame.winfo_children():
                            if isinstance(child, tk.Button):
                                copy_button = child
                                break

                        if copy_button:
                            button_req_height = copy_button.winfo_reqheight()
                            button_actual_height = copy_button.winfo_height()
                            print(f"  copy_button: {button_req_height}px → {button_actual_height}px")
                    except:
                        print(f"  copy_button: 取得エラー")

                print("=" * 60)
            else:
                print("[DEBUG] source_frameまたはresult_frameが見つかりません")

        except Exception as e:
            print(f"[DEBUG] 手動デバッグ表示エラー: {e}")

    def _wait_for_debug_input(self):
        """ターミナルで「a」入力を待機"""
        try:
            while self.window and self.window.winfo_exists():
                user_input = input()
                if user_input.strip().lower() == 'a':
                    self._debug_frame_heights_manual()
                elif user_input.strip().lower() == 'q':
                    print("デバッグ入力終了")
                    break
        except (EOFError, KeyboardInterrupt):
            # 入力終了時は何もしない
            pass
        except Exception as e:
            print(f"[DEBUG] 入力待機エラー: {e}")


    def _on_window_resize(self, event):
        """ウィンドウリサイズ時のレイアウト調整"""
        # ウィンドウ自体のリサイズのみ処理（子ウィジェットのリサイズは無視）
        if event.widget == self.window:
            try:
                # 現在のウィンドウサイズを取得
                current_width = self.window.winfo_width()
                current_height = self.window.winfo_height()

                # 前回のサイズと比較（初回は実行）
                if not hasattr(self, '_last_window_size'):
                    self._last_window_size = (current_width, current_height)
                    self.window.after(100, self._adjust_layout_on_resize)
                    return

                last_width, last_height = self._last_window_size

                # サイズが実際に変更された場合のみレイアウト調整を実行
                if current_width != last_width or current_height != last_height:
                    self._last_window_size = (current_width, current_height)

                    # デバウンス処理：既存のタイマーをキャンセルしてから新しいタイマーを設定
                    if hasattr(self, '_resize_timer'):
                        self.window.after_cancel(self._resize_timer)

                    # 少し遅延させてからレイアウト調整を実行（デバウンス）
                    self._resize_timer = self.window.after(150, self._adjust_layout_on_resize)
                    # print(f"[DEBUG] ウィンドウサイズ変更検出: {last_width}x{last_height} → {current_width}x{current_height}")  # 軽量化のためコメントアウト
                # サイズ変更がない場合は何もしない（ウィンドウ移動のみの場合）

            except Exception as e:
                print(f"[DEBUG] ウィンドウリサイズ処理エラー: {e}")

    def _adjust_layout_on_resize(self):
        """リサイズ時のレイアウト調整（分割バー廃止対応）"""
        try:
            if not self.window or not self.window.winfo_exists():
                return

            # ウィンドウの現在の高さを取得
            window_height = self.window.winfo_height()

            # 分割バー廃止：フレームをパック順序で検索
            source_frame = None
            result_frame = None
            button_frame = None

            # パック順序でフレームを取得（button_frameが最下部）
            children = list(self.window.winfo_children())

            # フレームをパック順序で検索（デバッグ色に依存しない方法）
            frame_count = 0
            for widget in children:
                if isinstance(widget, tk.Frame):
                    if frame_count == 0:
                        button_frame = widget  # 最初のフレーム（最下部に配置）
                    elif frame_count == 1:
                        source_frame = widget  # 2番目のフレーム
                    elif frame_count == 2:
                        result_frame = widget  # 3番目のフレーム
                    frame_count += 1

            if source_frame and result_frame:
                # button_frameの高さを取得
                button_frame_height = 35  # デフォルト値
                if button_frame:
                    button_frame_height = button_frame.winfo_reqheight()

                # 利用可能な高さを計算（パディング・余白を考慮）
                padding_and_margin = 60  # padx=20*2 + pady=5 + margin=15
                available_height = max(100, window_height - button_frame_height - padding_and_margin)

                # 原文縮小状態を確認
                is_collapsed = not self.source_expanded.get()

                if is_collapsed:
                    # 縮小状態：source_frameは最小高さ、result_frameは残りスペース
                    source_frame.configure(height=35)
                    result_frame.configure(height=available_height - 35)
                    # print(f"[DEBUG] リサイズ時縮小状態: source=35px, result={available_height - 35}px")  # 軽量化のためコメントアウト
                else:
                    # 展開状態：高さ均等化
                    frame_height = available_height // 2
                    source_frame.configure(height=frame_height)
                    result_frame.configure(height=frame_height)
                    # print(f"[DEBUG] リサイズ時展開状態（高さ均等化）: source={frame_height}px, result={frame_height}px")  # 軽量化のためコメントアウト

                # フレームの更新を強制（軽量化のため1回のみ）
                self.window.update_idletasks()
        except Exception as e:
            print(f"[DEBUG] レイアウト調整エラー: {e}")

    def _setup_error_display(self, error_message: str):
        """エラー表示の設定"""
        # メインフレーム
        main_frame = tk.Frame(self.window, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # アイコン表示
        icon_label = tk.Label(
            main_frame,
            text="⚠️",
            font=("Arial", 24),
            bg="#f8f9fa",
            fg="#dc3545"
        )
        icon_label.pack(pady=(0, 10))

        # エラータイトル
        title_label = tk.Label(
            main_frame,
            text="翻訳エラー",
            font=self.title_font,
            bg="#f8f9fa",
            fg="#dc3545"
        )
        title_label.pack(pady=(0, 10))

        # エラーメッセージ
        error_text = scrolledtext.ScrolledText(
            main_frame,
            height=8,
            wrap=tk.WORD,
            font=self.default_font,
            bg="#ffffff",
            fg="#dc3545",
            relief=tk.FLAT,
            borderwidth=1
        )
        error_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        error_text.insert("1.0", error_message)
        error_text.config(state=tk.DISABLED)

        # ボタンフレーム
        button_frame = tk.Frame(main_frame, bg="#f8f9fa")
        button_frame.pack(fill=tk.X)

    def _update_status_message(self, message: str):
        """ステータスメッセージの更新"""
        if self.window and self.window.winfo_exists():
            # 既存のステータスラベルを更新
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and "翻訳中" in str(child.cget("text")):
                            child.config(text=message)
                            break

    def _update_translation_display(self, result: TranslationResult):
        """翻訳結果表示の更新"""
        if self.window and self.window.winfo_exists():
            # 既存のウィンドウを破棄して新しく作成
            self.window.destroy()
            self._create_popup_window()
            self._setup_translation_display(result)
            self._position_window()
            self._show_window()

    def _position_window(self):
        """ウィンドウの位置を設定（マウス位置に表示）"""
        if not self.window:
            return

        try:
            # マウス位置を取得
            mouse_x, mouse_y = self.display_manager.get_mouse_position()

            # ポップアップの最適な位置を計算
            popup_x, popup_y = self.display_manager.calculate_popup_position(
                self.config.width, self.config.height, mouse_x, mouse_y
            )

            # ウィンドウ位置を設定
            self.window.geometry(f"{self.config.width}x{self.config.height}+{popup_x}+{popup_y}")

            print(f"ポップアップ位置設定: マウス({mouse_x}, {mouse_y}) -> ウィンドウ({popup_x}, {popup_y})")

        except Exception as e:
            print(f"マウス位置表示エラー: {e}")
            # フォールバック: 画面中央に表示
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = (screen_width - self.config.width) // 2 + self.config.offset_x
            y = (screen_height - self.config.height) // 2 + self.config.offset_y
            self.window.geometry(f"{self.config.width}x{self.config.height}+{x}+{y}")

    def _show_window(self):
        """ウィンドウを表示"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def _copy_result(self, text: str):
        """翻訳結果をクリップボードにコピー"""
        try:
            self.clipboard_manager.set_content(text)
            # 簡単なフィードバック
            if self.window and self.window.winfo_exists():
                # ボタンテキストを一時的に変更
                for widget in self.window.winfo_children():
                    if isinstance(widget, tk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Button) and "コピー" in str(child.cget("text")):
                                original_text = child.cget("text")
                                child.config(text="コピー完了！")
                                self.window.after(1000, lambda: child.config(text=original_text))
                                break
            print("翻訳結果をクリップボードにコピーしました")
        except Exception as e:
            print(f"クリップボードコピーエラー: {e}")
            messagebox.showerror("エラー", f"クリップボードへのコピーに失敗しました: {e}")

    def _start_status_timeout(self, timeout: float):
        """ステータス表示タイムアウトを開始"""
        self._stop_events['status'].clear()
        self._status_thread = threading.Thread(
            target=self._status_timeout_task,
            args=(timeout,),
            daemon=True
        )
        self._status_thread.start()

    def _status_timeout_task(self, timeout: float):
        """ステータスタイムアウトタスク"""
        if self._stop_events['status'].wait(timeout):
            return  # 停止イベントが発生

        # タイムアウト - ステータス表示を継続
        if self.state == PopupState.STATUS_DISPLAY:
            self.window.after(0, lambda: self._update_status_message("翻訳に時間がかかっています..."))

    def _start_auto_close_timer(self):
        """自動閉じるタイマーを開始"""
        self._stop_events['auto_close'].clear()
        self._auto_close_thread = threading.Thread(
            target=self._auto_close_task,
            daemon=True
        )
        self._auto_close_thread.start()

    def _auto_close_task(self):
        """自動閉じるタスク"""
        if self._stop_events['auto_close'].wait(self.config.auto_close_delay):
            return  # 停止イベントが発生

        # 自動閉じる（メインスレッドで実行）
        try:
            if self.window and self.window.winfo_exists():
                self.window.after(0, self.hide_popup)
        except Exception as e:
            print(f"ポップアップ自動閉じるエラー: {e}")

    def _stop_all_threads(self):
        """全スレッドを停止"""
        for event in self._stop_events.values():
            event.set()

    def _on_window_close(self):
        """ウィンドウ閉じる時のイベント"""
        self.hide_popup()

    def _handle_error(self, error_message: str):
        """エラー処理"""
        print(f"ポップアップエラー: {error_message}")
        # エラーポップアップを表示
        self.show_error_popup(error_message)

    def is_visible(self) -> bool:
        """ポップアップが表示中かどうか"""
        return (self.window is not None and
                self.window.winfo_exists() and
                self.state != PopupState.HIDDEN)

    def get_current_state(self) -> PopupState:
        """現在の状態を取得"""
        return self.state


if __name__ == "__main__":
    # テストコード
    print("=== PopupWindow テスト ===")

    from data.config import ConfigManager

    try:
        # 設定と言語管理の初期化
        config_manager = ConfigManager()
        language_manager = LanguageManager()

        # ポップアップウィンドウの作成
        popup = PopupWindow(config_manager, language_manager)

        # テスト用のルートウィンドウ
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを非表示

        # ステータスポップアップのテスト
        popup.show_status_popup("翻訳中...")

        # 3秒後に翻訳結果ポップアップを表示
        def show_result():
            from core.translation_manager import TranslationResult, TranslationStatus
            import time
            result = TranslationResult(
                source_text="Hello, world!",
                translated_text="こんにちは、世界！",
                source_language="en",
                target_language="ja",
                status=TranslationStatus.COMPLETED,
                timestamp=time.time(),
                processing_time=1.5
            )
            popup.show_translation_popup(result)

        root.after(3000, show_result)

        # 10秒後にウィンドウを閉じる
        root.after(10000, root.quit)

        root.mainloop()

    except Exception as e:
        print(f"ポップアップテストエラー: {e}")
        import traceback
        traceback.print_exc()
