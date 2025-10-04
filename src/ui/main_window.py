"""
Main Window - メインウィンドウUI

TkinterベースのメインウィンドウとUIコンポーネント
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.translation_manager import TranslationManager, TranslationStatus, TranslationResult
from core.clipboard_manager import ClipboardManager, ClipboardContent
from data.language import LanguageManager
from .components.split_pane import SplitPane


@dataclass
class UITheme:
    """UIテーマ設定"""
    # カラーテーマ
    bg_color: str
    fg_color: str
    text_bg_color: str
    button_bg_color: str
    button_fg_color: str
    entry_bg_color: str
    entry_fg_color: str
    border_color: str

    # フォント設定
    font_family: str
    font_size: int
    font_size_large: int


class MainWindow:
    """メインウィンドウクラス"""

    def __init__(self, config_manager, language_manager: LanguageManager):
        """
        メインウィンドウの初期化

        Args:
            config_manager: 設定管理オブジェクト
            language_manager: 言語管理オブジェクト
        """
        self.config_manager = config_manager
        self.language_manager = language_manager

        # 翻訳・クリップボード管理
        self.translation_manager = TranslationManager()
        self.clipboard_manager = ClipboardManager()

        # UI状態
        self.current_theme = "light"
        self.is_resizing = False
        self.translation_in_progress = False

        # 分割パネル
        self.split_pane: Optional[SplitPane] = None

        # ウィンドウ作成
        self.root = tk.Tk()
        self.setup_window()

        # テーマ設定
        self.setup_themes()

        # UIコンポーネント作成
        self.create_widgets()

        # イベントバインド
        self.bind_events()

        # コールバック設定
        self.setup_callbacks()

        print("メインウィンドウ初期化完了")

    def setup_window(self):
        """ウィンドウの基本設定"""
        self.root.title("CCTranslation")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # ウィンドウのアイコン設定（後で実装）
        # self.root.iconbitmap("icon/CCT_icon.ico")

        # ウィンドウのプロトコル設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ウィンドウを非表示で作成（ポップアップ用）
        self.root.withdraw()

    def setup_themes(self):
        """テーマ設定"""
        self.themes = {
            "light": UITheme(
                bg_color="#ffffff",
                fg_color="#000000",
                text_bg_color="#f8f9fa",
                button_bg_color="#e9ecef",
                button_fg_color="#000000",
                entry_bg_color="#ffffff",
                entry_fg_color="#000000",
                border_color="#dee2e6",
                font_family="Noto Sans JP",
                font_size=10,
                font_size_large=12
            ),
            "dark": UITheme(
                bg_color="#212529",
                fg_color="#ffffff",
                text_bg_color="#343a40",
                button_bg_color="#495057",
                button_fg_color="#ffffff",
                entry_bg_color="#495057",
                entry_fg_color="#ffffff",
                border_color="#6c757d",
                font_family="Noto Sans JP",
                font_size=10,
                font_size_large=12
            )
        }

    def create_widgets(self):
        """UIコンポーネントの作成"""
        # メインフレーム
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 上部コントロールフレーム
        self.create_control_frame()

        # 中央のテキストエリアフレーム
        self.create_text_frame()

        # 下部ボタンフレーム
        self.create_button_frame()

        # ステータスバー
        self.create_status_bar()

    def create_control_frame(self):
        """コントロールフレームの作成"""
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        # 翻訳元言語選択
        ttk.Label(self.control_frame, text="翻訳元:").pack(side=tk.LEFT, padx=(0, 5))
        self.source_lang_var = tk.StringVar(value="auto")
        self.source_lang_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.source_lang_var,
            width=15,
            state="readonly"
        )
        self.source_lang_combo.pack(side=tk.LEFT, padx=(0, 20))

        # 翻訳先言語選択
        ttk.Label(self.control_frame, text="翻訳先:").pack(side=tk.LEFT, padx=(0, 5))
        self.target_lang_var = tk.StringVar(value="ja")
        self.target_lang_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.target_lang_var,
            width=15,
            state="readonly"
        )
        self.target_lang_combo.pack(side=tk.LEFT, padx=(0, 20))

        # テーマ切り替えボタン
        self.theme_button = ttk.Button(
            self.control_frame,
            text="ダークモード",
            command=self.toggle_theme
        )
        self.theme_button.pack(side=tk.RIGHT)

        # 言語リストを設定
        self.update_language_lists()

    def create_text_frame(self):
        """テキストエリアフレームの作成（分割パネル使用）"""
        self.text_frame = ttk.Frame(self.main_frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 分割パネルを作成
        self.split_pane = SplitPane(self.text_frame, orientation='vertical')
        self.split_pane.pack(fill=tk.BOTH, expand=True)
        print(f"[DEBUG] 分割パネル作成完了: {self.split_pane}")

        # 翻訳元テキストエリア
        self.create_source_text_area()

        # 翻訳先テキストエリア
        self.create_target_text_area()

    def create_source_text_area(self):
        """翻訳元テキストエリアの作成"""
        # フレームを作成（親はSplitPaneのpaned_window）
        source_frame = ttk.LabelFrame(self.split_pane.paned_window, text="翻訳元テキスト")

        self.source_text = scrolledtext.ScrolledText(
            source_frame,
            height=8,
            wrap=tk.WORD,
            font=(self.themes[self.current_theme].font_family,
                  self.themes[self.current_theme].font_size)
        )
        self.source_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 分割パネルに追加
        if self.split_pane:
            self.split_pane.add_pane(source_frame, weight=1, min_size=100)

    def create_target_text_area(self):
        """翻訳先テキストエリアの作成"""
        # フレームを作成（親はSplitPaneのpaned_window）
        target_frame = ttk.LabelFrame(self.split_pane.paned_window, text="翻訳結果")

        self.target_text = scrolledtext.ScrolledText(
            target_frame,
            height=8,
            wrap=tk.WORD,
            font=(self.themes[self.current_theme].font_family,
                  self.themes[self.current_theme].font_size),
            state=tk.DISABLED
        )
        self.target_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 分割パネルに追加
        if self.split_pane:
            self.split_pane.add_pane(target_frame, weight=1, min_size=100)

            # 分割バーのドラッグイベントをバインド
            self.split_pane.bind_sash_motion(self.on_sash_motion)
            print("[DEBUG] 分割バーイベントバインド完了")

            # ウィンドウ表示後に分割バーの初期位置を設定（より長い待機時間）
            self.root.after(500, self._setup_split_pane_after_display)

    def _setup_split_pane_after_display(self):
        """ウィンドウ表示後の分割バーセットアップ"""
        try:
            # ウィンドウが完全に表示されるまで待機
            self.root.update_idletasks()

            # 分割バーの初期位置を設定（ウィンドウの中央）
            self.split_pane.set_initial_sash_position()

            # 分割バーの詳細情報を確認
            self.split_pane.debug_sash_info()

            print("[DEBUG] 分割バーセットアップ完了")
        except Exception as e:
            print(f"[DEBUG] 分割バーセットアップエラー: {e}")

    def on_sash_motion(self, sash_index: int, position: int):
        """分割バードラッグ時のコールバック"""
        print(f"[DEBUG] 分割バードラッグ: sash_index={sash_index}, position={position}")

    def create_button_frame(self):
        """ボタンフレームの作成"""
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(0, 10))

        # 翻訳ボタン
        self.translate_button = ttk.Button(
            self.button_frame,
            text="翻訳実行",
            command=self.translate_text,
            state=tk.DISABLED
        )
        self.translate_button.pack(side=tk.LEFT, padx=(0, 10))

        # クリップボードから読み込みボタン
        self.load_button = ttk.Button(
            self.button_frame,
            text="クリップボードから読み込み",
            command=self.load_from_clipboard
        )
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))

        # 翻訳結果をクリップボードにコピーボタン
        self.copy_button = ttk.Button(
            self.button_frame,
            text="結果をクリップボードにコピー",
            command=self.copy_result_to_clipboard,
            state=tk.DISABLED
        )
        self.copy_button.pack(side=tk.RIGHT)

    def create_status_bar(self):
        """ステータスバーの作成"""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(
            self.status_frame,
            text="準備完了",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)

    def update_language_lists(self):
        """言語リストの更新"""
        try:
            languages = self.language_manager.get_language_list()

            # 翻訳元言語リスト（自動検出を含む）
            source_languages = [("auto", "自動検出")] + languages
            source_display = [f"{name} ({code})" for code, name in source_languages]
            self.source_lang_combo['values'] = source_display

            # 翻訳先言語リスト
            target_display = [f"{name} ({code})" for code, name in languages]
            self.target_lang_combo['values'] = target_display

            print("言語リストを更新しました")

        except Exception as e:
            print(f"言語リスト更新エラー: {e}")
            messagebox.showerror("エラー", f"言語リストの読み込みに失敗しました: {e}")

    def bind_events(self):
        """イベントのバインド"""
        # テキスト変更イベント
        self.source_text.bind('<KeyRelease>', self.on_source_text_changed)

        # ウィンドウリサイズイベント
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_callbacks(self):
        """コールバック関数の設定"""
        # 翻訳状態変更コールバック
        self.translation_manager.set_status_callback(self.on_translation_status_changed)

        # 翻訳完了コールバック
        self.translation_manager.set_completion_callback(self.on_translation_completed)

    def toggle_theme(self):
        """テーマの切り替え"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.config(text="ライトモード")
        else:
            self.current_theme = "light"
            self.theme_button.config(text="ダークモード")

        self.apply_theme()

    def apply_theme(self):
        """テーマの適用"""
        theme = self.themes[self.current_theme]

        try:
            # ウィンドウの背景色
            self.root.configure(bg=theme.bg_color)

            # テキストエリアの色設定
            self.source_text.configure(
                bg=theme.text_bg_color,
                fg=theme.fg_color,
                insertbackground=theme.fg_color
            )

            self.target_text.configure(
                bg=theme.text_bg_color,
                fg=theme.fg_color,
                insertbackground=theme.fg_color
            )

            # フォント設定
            font = (theme.font_family, theme.font_size)
            self.source_text.configure(font=font)
            self.target_text.configure(font=font)

            print(f"テーマを {self.current_theme} に切り替えました")

        except Exception as e:
            print(f"テーマ適用エラー: {e}")

    def on_source_text_changed(self, event):
        """翻訳元テキスト変更時のイベント"""
        text = self.source_text.get("1.0", tk.END).strip()

        # 翻訳ボタンの状態を更新
        if text and not self.translation_in_progress:
            self.translate_button.config(state=tk.NORMAL)
        else:
            self.translate_button.config(state=tk.DISABLED)

    def on_window_resize(self, event):
        """ウィンドウリサイズ時のイベント"""
        if event.widget == self.root and not self.is_resizing:
            self.is_resizing = True
            self.root.after(100, self.finish_resize)

    def finish_resize(self):
        """リサイズ完了処理"""
        self.is_resizing = False
        # 必要に応じてレイアウト調整

    def translate_text(self):
        """翻訳実行"""
        source_text = self.source_text.get("1.0", tk.END).strip()
        if not source_text:
            return

        # 言語選択の取得
        source_lang = self.get_selected_language_code(self.source_lang_var.get())
        target_lang = self.get_selected_language_code(self.target_lang_var.get())

        # 翻訳状態を更新
        self.translation_in_progress = True
        self.translate_button.config(state=tk.DISABLED)
        self.status_label.config(text="翻訳中...")

        # 非同期翻訳実行
        threading.Thread(
            target=self._perform_translation,
            args=(source_text, source_lang, target_lang),
            daemon=True
        ).start()

    def _perform_translation(self, text: str, source_lang: str, target_lang: str):
        """翻訳実行（別スレッド）"""
        try:
            self.translation_manager.translate_async(text, target_lang, source_lang)
            result = self.translation_manager.wait_for_completion(timeout=5.0)

            if result:
                self.root.after(0, self._update_translation_result, result)
            else:
                self.root.after(0, self._handle_translation_timeout)

        except Exception as e:
            self.root.after(0, self._handle_translation_error, str(e))

    def _update_translation_result(self, result: TranslationResult):
        """翻訳結果の更新（UIスレッド）"""
        if result.status == TranslationStatus.COMPLETED:
            self.target_text.config(state=tk.NORMAL)
            self.target_text.delete("1.0", tk.END)
            self.target_text.insert("1.0", result.translated_text)
            self.target_text.config(state=tk.DISABLED)

            self.copy_button.config(state=tk.NORMAL)
            self.status_label.config(text="翻訳完了")
        else:
            self.status_label.config(text=f"翻訳エラー: {result.error_message}")

        self.translation_in_progress = False
        self.translate_button.config(state=tk.NORMAL)

    def _handle_translation_timeout(self):
        """翻訳タイムアウト処理（UIスレッド）"""
        self.status_label.config(text="翻訳がタイムアウトしました")
        self.translation_in_progress = False
        self.translate_button.config(state=tk.NORMAL)

    def _handle_translation_error(self, error_message: str):
        """翻訳エラー処理（UIスレッド）"""
        self.status_label.config(text=f"翻訳エラー: {error_message}")
        self.translation_in_progress = False
        self.translate_button.config(state=tk.NORMAL)

    def on_translation_status_changed(self, status: TranslationStatus, result: Optional[TranslationResult]):
        """翻訳状態変更コールバック"""
        status_texts = {
            TranslationStatus.IDLE: "待機中",
            TranslationStatus.TRANSLATING: "翻訳中...",
            TranslationStatus.COMPLETED: "翻訳完了",
            TranslationStatus.TIMEOUT: "タイムアウト",
            TranslationStatus.ERROR: "エラー"
        }

        self.root.after(0, lambda: self.status_label.config(text=status_texts.get(status, "不明")))

    def on_translation_completed(self, result: TranslationResult):
        """翻訳完了コールバック"""
        self.root.after(0, self._update_translation_result, result)

    def load_from_clipboard(self):
        """クリップボードから読み込み"""
        try:
            text = self.clipboard_manager.get_text_for_translation()
            if text:
                self.source_text.delete("1.0", tk.END)
                self.source_text.insert("1.0", text)
                self.status_label.config(text="クリップボードから読み込み完了")
                self.on_source_text_changed(None)  # 翻訳ボタンの状態を更新
            else:
                self.status_label.config(text="クリップボードが空です")

        except Exception as e:
            messagebox.showerror("エラー", f"クリップボードからの読み込みに失敗しました: {e}")
            self.status_label.config(text="クリップボード読み込みエラー")

    def copy_result_to_clipboard(self):
        """翻訳結果をクリップボードにコピー"""
        try:
            result_text = self.target_text.get("1.0", tk.END).strip()
            if result_text:
                self.clipboard_manager.set_content(result_text)
                self.status_label.config(text="結果をクリップボードにコピーしました")
            else:
                self.status_label.config(text="コピーする結果がありません")

        except Exception as e:
            messagebox.showerror("エラー", f"クリップボードへのコピーに失敗しました: {e}")
            self.status_label.config(text="クリップボードコピーエラー")

    def get_selected_language_code(self, display_text: str) -> str:
        """表示テキストから言語コードを取得"""
        if "(" in display_text and ")" in display_text:
            return display_text.split("(")[-1].rstrip(")")
        return display_text

    def on_closing(self):
        """ウィンドウ終了時の処理"""
        try:
            # 翻訳処理をキャンセル
            self.translation_manager.cancel_translation()

            # 設定保存
            self.config_manager.set("ui", "theme", self.current_theme)
            self.config_manager.set("ui", "source_language", self.source_lang_var.get())
            self.config_manager.set("ui", "target_language", self.target_lang_var.get())

            print("設定を保存しました")

        except Exception as e:
            print(f"設定保存エラー: {e}")

        finally:
            self.root.destroy()

    def run(self):
        """ウィンドウの実行"""
        self.root.mainloop()

    def show(self):
        """ウィンドウの表示"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()


if __name__ == "__main__":
    # テストコード
    print("=== MainWindow テスト ===")

    # 必要なモジュールのインポート
    from data.config import ConfigManager

    try:
        # 設定と言語管理の初期化
        config_manager = ConfigManager()
        language_manager = LanguageManager()

        # メインウィンドウの作成と実行
        app = MainWindow(config_manager, language_manager)
        app.run()

    except Exception as e:
        print(f"アプリケーション実行エラー: {e}")
        import traceback
        traceback.print_exc()
