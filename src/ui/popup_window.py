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
    min_height: int = 600

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
        self.window.minsize(self.config.min_width, self.config.min_height)


        # ウィンドウの設定
        self.window.transient()  # 親ウィンドウに対する子ウィンドウとして設定
        self.window.grab_set()   # モーダルウィンドウとして設定
        self.window.resizable(True, True)

        # ウィンドウプロトコル設定
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # エスケープキーでウィンドウを閉じる機能を追加
        self.window.bind('<Escape>', lambda event: self.hide_popup())

        # ウィンドウリサイズ時のレイアウト調整
        self.window.bind('<Configure>', self._on_window_resize)

        # スタイル設定
        self.window.configure(bg="#f8f9fa")

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
        # 分割パネル（PanedWindow）を作成
        # ボタンエリアの高さ（約60px）を考慮してPanedWindowの高さを動的に計算
        def calculate_paned_height():
            window_height = self.window.winfo_height()
            # ボタンエリア（60px）+ パディング（40px）+ 安全マージン（20px）= 120px
            available_height = max(300, window_height - 120)
            return available_height

        paned_window = tk.PanedWindow(self.window, orient='vertical')
        paned_window.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 0))

        # 初期高さを設定
        paned_window.configure(height=calculate_paned_height())

        # 翻訳元テキスト（展開/縮小可能）
        source_frame = tk.Frame(paned_window, bg="green", relief=tk.FLAT)  # デバッグ用に緑色
        source_frame.pack_propagate(False)  # 子ウィジェットのサイズに依存しない

        # 原文ヘッダー（クリック可能）
        source_header = tk.Frame(source_frame, bg="#f8f9fa", height=35, relief=tk.FLAT)
        source_header.pack(fill=tk.X, padx=10, pady=(8, 0))
        source_header.pack_propagate(False)

        # 展開/縮小状態を管理
        source_expanded = tk.BooleanVar(value=True)  # デフォルトは展開状態


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

                # 原文エリアの最小サイズ制限を解除（縮小時は制限なし）
                paned_window.paneconfig(source_frame, minsize=0)

                # 分割バーを上に移動（原文エリアが無くなった分）
                paned_window.after(100, lambda: adjust_sash_for_collapsed())
            else:
                # 展開状態に切り替え
                source_expanded.set(True)
                source_label.config(text=f"▼ 原文 ({result.source_language})")
                source_text_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 8))  # テキストボックス部分を表示
                # 高さ制限を解除
                source_frame.configure(height=400)

                # 原文エリアの最小サイズ制限を復元（展開時は制限あり）
                min_source_pane_height = max(80, self.config.min_height // 8)
                paned_window.paneconfig(source_frame, minsize=min_source_pane_height)

                # 分割バーを中央に戻す
                paned_window.after(100, lambda: adjust_sash_for_expanded())

        def adjust_sash_for_collapsed():
            """縮小時の分割バー位置調整"""
            try:
                paned_window.update_idletasks()
                height = paned_window.winfo_height()
                if height > 1:
                    # 縮小時は原文テキストエリアが非表示になった分だけ分割バーを上に移動
                    # 原文テキストエリアの高さを動的に計算
                    # 展開時の中央位置から原文テキストエリアの高さ分を引く
                    original_sash_pos = height // 2  # 展開時の中央位置
                    # 原文テキストエリアの高さは、展開時の上部エリアの高さからヘッダー分（35px）を引いた値
                    source_text_height = original_sash_pos - 35  # ヘッダー分を除いた原文テキストエリアの高さ
                    new_pos = max(35, original_sash_pos - source_text_height)  # 最小35px（ヘッダー分）
                    paned_window.sash_place(0, 0, new_pos)
                    print(f"[DEBUG] 縮小時分割バー位置調整: {new_pos} (原文テキストエリア非表示分{source_text_height}px上に移動)")
            except Exception as e:
                print(f"[DEBUG] 縮小時分割バー調整エラー: {e}")

        def adjust_sash_for_expanded():
            """展開時の分割バー位置調整"""
            try:
                paned_window.update_idletasks()
                height = paned_window.winfo_height()
                if height > 1:
                    # 展開時は分割バーを中央に配置（最小サイズを考慮）
                    # 各エリアの最小サイズを確保できるよう調整
                    min_source_size = max(80, self.config.min_height // 8)  # 原文エリア
                    min_result_size = 40  # 翻訳結果エリア（1行分）
                    center_pos = height // 2

                    # 最小サイズを保証しながら中央配置
                    if center_pos < min_source_size:
                        new_pos = min_source_size
                    elif height - center_pos < min_result_size:
                        new_pos = height - min_result_size
                    else:
                        new_pos = center_pos

                    paned_window.sash_place(0, 0, new_pos)
                    print(f"[DEBUG] 展開時分割バー位置調整: {new_pos}")
            except Exception as e:
                print(f"[DEBUG] 展開時分割バー調整エラー: {e}")

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
        result_frame = tk.Frame(paned_window, bg="yellow", relief=tk.FLAT)  # デバッグ用に黄色

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
        paned_window.add(source_frame)
        paned_window.add(result_frame)

        # 各ペインの最小サイズを設定（requirements.mdの仕様に準拠）
        # 原文エリア：動的計算（展開時のみ適用）
        min_source_pane_height = max(80, self.config.min_height // 8)
        # 翻訳結果エリア：1行分の高さ（requirements.md仕様）
        min_result_pane_height = 40  # テキスト1行分の高さ（フォントサイズ + パディング + 安全マージン）

        paned_window.paneconfig(source_frame, minsize=min_source_pane_height)  # 原文エリア最小高さ
        paned_window.paneconfig(result_frame, minsize=min_result_pane_height)  # 翻訳結果エリア最小高さ（1行）

        # 分割バーの初期位置を設定（中央）
        paned_window.after(100, lambda: self._set_paned_window_sash_position(paned_window))

        # ボタンフレーム（最小高さを保証）- ウィンドウに直接配置
        button_frame = tk.Frame(self.window, bg="red", height=60)  # デバッグ用に赤色
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20)
        button_frame.pack_propagate(False)  # 子ウィジェットのサイズに依存しない

        # コピーボタン
        copy_button = tk.Button(
            button_frame,
            text="結果をコピー",
            font=self.default_font,
            command=lambda: self._copy_result(result.translated_text),
            bg="#007bff",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        copy_button.pack(side=tk.LEFT, padx=(0, 10))

        # 閉じるボタン
        close_button = tk.Button(
            button_frame,
            text="閉じる",
            font=self.default_font,
            command=self.hide_popup,
            bg="#6c757d",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        close_button.pack(side=tk.RIGHT)

    def _set_paned_window_sash_position(self, paned_window):
        """PanedWindowの分割バーの初期位置を設定"""
        try:
            # ウィンドウが完全に表示されるまで待機
            paned_window.update_idletasks()

            # 高さを取得して中央に設定（最小サイズを考慮）
            height = paned_window.winfo_height()
            if height > 1:
                # 各エリアの最小サイズを確保できるよう調整
                min_source_size = max(80, self.config.min_height // 8)  # 原文エリア
                min_result_size = 25  # 翻訳結果エリア（1行分）
                center_pos = height // 2

                # 最小サイズを保証しながら中央配置
                if center_pos < min_source_size:
                    initial_pos = min_source_size
                elif height - center_pos < min_result_size:
                    initial_pos = height - min_result_size
                else:
                    initial_pos = center_pos

                paned_window.sash_place(0, 0, initial_pos)
                print(f"[DEBUG] ポップアップ分割バー位置設定: {initial_pos} (高さ: {height})")
            else:
                # サイズが取得できない場合は少し待って再試行
                paned_window.after(100, lambda: self._set_paned_window_sash_position(paned_window))
        except Exception as e:
            print(f"[DEBUG] ポップアップ分割バー位置設定エラー: {e}")

    def _on_window_resize(self, event):
        """ウィンドウリサイズ時のレイアウト調整"""
        # ウィンドウ自体のリサイズのみ処理（子ウィジェットのリサイズは無視）
        if event.widget == self.window:
            try:

                # 少し遅延させてからレイアウト調整を実行
                self.window.after(100, self._adjust_layout_on_resize)
            except Exception as e:
                print(f"[DEBUG] ウィンドウリサイズ処理エラー: {e}")

    def _adjust_layout_on_resize(self):
        """リサイズ時のレイアウト調整"""
        try:
            if not self.window or not self.window.winfo_exists():
                return

            # ウィンドウの現在の高さを取得
            window_height = self.window.winfo_height()

            # メインフレーム内のPanedWindowを検索
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Frame) and widget.cget('bg') == '#f8f9fa':
                    # メインフレーム内のPanedWindowを検索
                    for child in widget.winfo_children():
                        if isinstance(child, tk.PanedWindow):
                            # ボタンエリア用に最低100px確保し、残りをPanedWindowに割り当て
                            available_height = max(300, window_height - 150)
                            child.configure(height=available_height)
                            print(f"[DEBUG] リサイズ時PanedWindow高さ調整: {available_height}")
                            break
                    break
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

        # 閉じるボタン
        close_button = tk.Button(
            button_frame,
            text="閉じる",
            font=self.default_font,
            command=self.hide_popup,
            bg="#dc3545",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        close_button.pack(side=tk.RIGHT)

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
