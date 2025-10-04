"""
System Tray - システムトレイ統合

システムトレイアイコン、メニュー、常駐アプリケーション機能
"""

import pystray
from pystray import MenuItem as Item, Menu as menu
from PIL import Image, ImageDraw
import threading
import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.config import ConfigManager
from data.language import LanguageManager
from ui.popup_window import PopupWindow
from ui.main_window import MainWindow


class SystemTrayManager:
    """システムトレイ管理クラス"""

    def __init__(self, config_manager: ConfigManager, language_manager: LanguageManager):
        """
        システムトレイ管理の初期化

        Args:
            config_manager: 設定管理オブジェクト
            language_manager: 言語管理オブジェクト
        """
        self.config_manager = config_manager
        self.language_manager = language_manager

        # システムトレイアイコン
        self.icon: Optional[pystray.Icon] = None
        self.icon_image: Optional[Image.Image] = None

        # UIコンポーネント
        self.main_window: Optional[MainWindow] = None
        self.popup_window: Optional[PopupWindow] = None

        # 状態管理
        self.is_running = False
        self.is_main_window_visible = False

        # コールバック
        self._on_show_main_window: Optional[Callable] = None
        self._on_exit_app: Optional[Callable] = None

        # アイコン作成
        self._create_icon_image()

        print("システムトレイ管理初期化完了")

    def set_callbacks(self,
                     on_show_main_window: Optional[Callable] = None,
                     on_exit_app: Optional[Callable] = None):
        """
        コールバック関数の設定

        Args:
            on_show_main_window: メインウィンドウ表示時のコールバック
            on_exit_app: アプリ終了時のコールバック
        """
        self._on_show_main_window = on_show_main_window
        self._on_exit_app = on_exit_app

    def _create_icon_image(self):
        """システムトレイアイコン画像の作成"""
        try:
            # アイコンファイルのパスを確認
            icon_path = Path("icon/CCT_icon.ico")
            if icon_path.exists():
                # 既存のアイコンファイルを使用
                self.icon_image = Image.open(icon_path)
                print(f"アイコンファイルを読み込みました: {icon_path}")
            else:
                # デフォルトアイコンを作成
                self._create_default_icon()
                print("デフォルトアイコンを作成しました")

        except Exception as e:
            print(f"アイコン読み込みエラー: {e}")
            self._create_default_icon()

    def _create_default_icon(self):
        """デフォルトアイコンを作成"""
        # 64x64のアイコンを作成
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 背景円
        draw.ellipse([8, 8, width-8, height-8], fill=(0, 123, 255, 255))

        # 翻訳アイコン（T）
        draw.text((width//2-8, height//2-12), "T", fill=(255, 255, 255, 255))

        # 小さい円（アクティブ状態を示す）
        draw.ellipse([width-20, height-20, width-12, height-12], fill=(255, 255, 255, 255))

        self.icon_image = image

    def create_menu(self) -> menu:
        """システムトレイメニューを作成"""
        return menu(
            Item(
                "CCTranslation",
                menu(
                    Item("メインウィンドウを表示", self._show_main_window),
                    Item("設定", self._show_settings),
                    Item("言語設定", self._show_language_settings),
                    menu.SEPARATOR,
                    Item("バージョン情報", self._show_version_info)
                )
            ),
            menu.SEPARATOR,
            Item("終了", self._exit_application)
        )

    def start_system_tray(self):
        """システムトレイを開始"""
        try:
            if self.is_running:
                print("システムトレイは既に実行中です")
                return

            # メニュー作成
            tray_menu = self.create_menu()

            # アイコン作成
            self.icon = pystray.Icon(
                "CCTranslation",
                self.icon_image,
                "CCTranslation - 翻訳ツール",
                tray_menu
            )

            # アイコンクリックイベント
            self.icon.run_detached = True
            self.icon.run_setup = self._on_icon_setup

            # システムトレイ開始
            self.is_running = True
            print("システムトレイを開始します...")

            # 別スレッドで実行
            tray_thread = threading.Thread(target=self._run_tray, daemon=True)
            tray_thread.start()

            print("システムトレイ開始完了")

        except Exception as e:
            print(f"システムトレイ開始エラー: {e}")
            self.is_running = False

    def _run_tray(self):
        """システムトレイを実行"""
        try:
            if self.icon:
                self.icon.run()
        except Exception as e:
            print(f"システムトレイ実行エラー: {e}")
        finally:
            self.is_running = False

    def _on_icon_setup(self, icon):
        """アイコンセットアップ時のコールバック"""
        icon.visible = True
        print("システムトレイアイコンが表示されました")

    def stop_system_tray(self):
        """システムトレイを停止"""
        try:
            if self.icon:
                self.icon.stop()
                self.icon = None

            self.is_running = False
            print("システムトレイを停止しました")

        except Exception as e:
            print(f"システムトレイ停止エラー: {e}")

    def _show_main_window(self, icon=None, item=None):
        """メインウィンドウを表示"""
        try:
            print("メインウィンドウ表示要求")

            if self._on_show_main_window:
                self._on_show_main_window()
            else:
                # デフォルトのメインウィンドウ表示
                if not self.main_window:
                    self.main_window = MainWindow(self.config_manager, self.language_manager)

                self.main_window.show()
                self.is_main_window_visible = True

        except Exception as e:
            print(f"メインウィンドウ表示エラー: {e}")

    def _show_settings(self, icon=None, item=None):
        """設定ウィンドウを表示"""
        try:
            print("設定ウィンドウ表示要求")
            # 設定ウィンドウの実装は後で追加

            # 暫定的にメインウィンドウを表示
            self._show_main_window()

        except Exception as e:
            print(f"設定ウィンドウ表示エラー: {e}")

    def _show_language_settings(self, icon=None, item=None):
        """言語設定ウィンドウを表示"""
        try:
            print("言語設定ウィンドウ表示要求")
            # 言語設定ウィンドウの実装は後で追加

            # 暫定的にメインウィンドウを表示
            self._show_main_window()

        except Exception as e:
            print(f"言語設定ウィンドウ表示エラー: {e}")

    def _show_version_info(self, icon=None, item=None):
        """バージョン情報を表示"""
        try:
            import tkinter as tk
            from tkinter import messagebox

            # ルートウィンドウを作成（非表示）
            root = tk.Tk()
            root.withdraw()

            version_info = f"""CCTranslation v1.0.0

翻訳ツール
Windows 常駐型翻訳アプリケーション

開発: CCTranslation Team
ライセンス: MIT License

機能:
• ダブルコピー検出翻訳
• Google翻訳API統合
• システムトレイ常駐
• 日本語キーボード対応"""

            messagebox.showinfo("バージョン情報", version_info)
            root.destroy()

        except Exception as e:
            print(f"バージョン情報表示エラー: {e}")

    def _exit_application(self, icon=None, item=None):
        """アプリケーションを終了"""
        try:
            print("アプリケーション終了要求")

            if self._on_exit_app:
                self._on_exit_app()
            else:
                # デフォルトの終了処理
                self.stop_system_tray()
                if self.main_window:
                    self.main_window.root.quit()
                if self.popup_window:
                    self.popup_window.hide_popup()

                print("アプリケーションを終了しました")

        except Exception as e:
            print(f"アプリケーション終了エラー: {e}")

    def update_icon_tooltip(self, tooltip: str):
        """アイコンのツールチップを更新"""
        try:
            if self.icon:
                self.icon.title = tooltip
                print(f"ツールチップを更新しました: {tooltip}")
        except Exception as e:
            print(f"ツールチップ更新エラー: {e}")

    def show_notification(self, title: str, message: str, duration: float = 3.0):
        """通知を表示（Windows通知機能は無効化）"""
        try:
            # Windows通知機能は無効化（requirements.mdの制約事項に従う）
            # 代わりにコンソールログのみ出力
            print(f"通知: {title} - {message}")
        except Exception as e:
            print(f"通知表示エラー: {e}")

    def set_main_window(self, main_window: MainWindow):
        """メインウィンドウを設定"""
        self.main_window = main_window

    def set_popup_window(self, popup_window: PopupWindow):
        """ポップアップウィンドウを設定"""
        self.popup_window = popup_window

    def set_callbacks(self, on_show_main_window=None, on_exit_app=None):
        """コールバック関数の設定"""
        self._on_show_main_window = on_show_main_window
        self._on_exit_app = on_exit_app

    def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        return {
            "is_running": self.is_running,
            "is_main_window_visible": self.is_main_window_visible,
            "icon_exists": self.icon is not None,
            "icon_image_exists": self.icon_image is not None
        }


class SystemTrayApp:
    """システムトレイアプリケーション統合クラス"""

    def __init__(self):
        """システムトレイアプリケーションの初期化"""
        # 管理オブジェクトの初期化
        self.config_manager = ConfigManager()
        self.language_manager = LanguageManager()

        # UIコンポーネント
        self.system_tray = SystemTrayManager(self.config_manager, self.language_manager)
        self.main_window: Optional[MainWindow] = None
        self.popup_window: Optional[PopupWindow] = None

        # アプリケーション状態
        self.is_running = False

        print("システムトレイアプリケーション初期化完了")

    def initialize_ui_components(self):
        """UIコンポーネントを初期化"""
        try:
            # ポップアップウィンドウの作成
            self.popup_window = PopupWindow(self.config_manager, self.language_manager)

            # メインウィンドウの作成（必要時のみ）
            # self.main_window = MainWindow(self.config_manager, self.language_manager)

            # システムトレイにUIコンポーネントを設定
            self.system_tray.set_popup_window(self.popup_window)
            if self.main_window:
                self.system_tray.set_main_window(self.main_window)

            print("UIコンポーネント初期化完了")

        except Exception as e:
            print(f"UIコンポーネント初期化エラー: {e}")

    def set_callbacks(self, on_show_main_window=None, on_exit_app=None):
        """コールバック関数の設定"""
        self.system_tray.set_callbacks(
            on_show_main_window=on_show_main_window,
            on_exit_app=on_exit_app
        )

    def start_application(self):
        """アプリケーションを開始"""
        try:
            if self.is_running:
                print("アプリケーションは既に実行中です")
                return

            # UIコンポーネントを初期化
            self.initialize_ui_components()

            # システムトレイのコールバックを設定
            self.system_tray.set_callbacks(
                on_show_main_window=self.show_main_window,
                on_exit_app=self.exit_application
            )

            # システムトレイを開始
            self.system_tray.start_system_tray()

            self.is_running = True
            print("アプリケーション開始完了")

            # 初回通知
            self.system_tray.show_notification(
                "CCTranslation",
                "翻訳ツールが開始されました",
                2.0
            )

        except Exception as e:
            print(f"アプリケーション開始エラー: {e}")
            self.is_running = False

    def show_main_window(self):
        """メインウィンドウを表示"""
        try:
            # 既存のメインウィンドウインスタンスがある場合はそれを使用
            if hasattr(self, '_external_main_window') and self._external_main_window:
                self._external_main_window.show()
                print("既存のメインウィンドウを表示しました")
            else:
                # 新しく作成
                if not self.main_window:
                    self.main_window = MainWindow(self.config_manager, self.language_manager)
                    self.system_tray.set_main_window(self.main_window)

                self.main_window.show()
                self.system_tray.is_main_window_visible = True
                print("新しいメインウィンドウを表示しました")

        except Exception as e:
            print(f"メインウィンドウ表示エラー: {e}")

    def set_main_window_instance(self, main_window):
        """外部からメインウィンドウインスタンスを設定"""
        self._external_main_window = main_window
        print("外部メインウィンドウインスタンスを設定しました")

    def exit_application(self):
        """アプリケーションを終了"""
        try:
            print("アプリケーション終了処理を開始します")

            # UIコンポーネントをクリーンアップ
            if self.popup_window:
                self.popup_window.hide_popup()

            if self.main_window:
                self.main_window.root.quit()
                self.main_window.root.destroy()

            # システムトレイを停止
            self.system_tray.stop_system_tray()

            self.is_running = False
            print("アプリケーション終了完了")

        except Exception as e:
            print(f"アプリケーション終了エラー: {e}")

    def get_status(self) -> Dict[str, Any]:
        """アプリケーション状態を取得"""
        status = {
            "is_running": self.is_running,
            "system_tray_status": self.system_tray.get_status() if self.system_tray else None,
            "main_window_exists": self.main_window is not None,
            "popup_window_exists": self.popup_window is not None
        }
        return status


if __name__ == "__main__":
    # テストコード
    print("=== SystemTray テスト ===")

    try:
        # システムトレイアプリケーションを作成
        app = SystemTrayApp()

        # アプリケーションを開始
        app.start_application()

        print("システムトレイが開始されました。")
        print("システムトレイアイコンを右クリックしてメニューを確認してください。")
        print("終了するには、メニューから「終了」を選択してください。")

        # メインループ（システムトレイは別スレッドで実行）
        try:
            while app.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nキーボード割り込みで終了します")
            app.exit_application()

    except Exception as e:
        print(f"システムトレイテストエラー: {e}")
        import traceback
        traceback.print_exc()
