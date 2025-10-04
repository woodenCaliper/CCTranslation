"""
CCTranslation - メインアプリケーション

Windows常駐型翻訳ユーティリティ
ダブルコピー検出から翻訳完了までの完全なワークフロー
"""

import sys
import os
import time
import threading
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.config import ConfigManager
from src.data.language import LanguageManager
from src.core.hotkey import HotkeyManager
from src.core.clipboard_manager import ClipboardManager
from src.core.translation_manager import TranslationManager, TranslationStatus, TranslationResult
from src.ui.popup_window import PopupWindow
from src.ui.main_window import MainWindow
from src.ui.system_tray import SystemTrayApp
from src.utils.exceptions import CCTranslationException, TranslationError, ClipboardError, HotkeyError
from src.utils.single_instance import SingleInstanceManager


class CCTranslationApp:
    """CCTranslation メインアプリケーションクラス"""

    def __init__(self):
        """アプリケーションの初期化"""
        self.is_running = False
        self.is_translating = False

        # 管理オブジェクト
        self.config_manager: Optional[ConfigManager] = None
        self.language_manager: Optional[LanguageManager] = None

        # コアコンポーネント
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.clipboard_manager: Optional[ClipboardManager] = None
        self.translation_manager: Optional[TranslationManager] = None

        # UIコンポーネント
        self.popup_window: Optional[PopupWindow] = None
        self.main_window: Optional[MainWindow] = None
        self.system_tray: Optional[SystemTrayApp] = None

        # 設定
        self.settings = {
            'source_language': 'auto',
            'target_language': 'ja',
            'double_copy_interval': 0.5,
            'translation_timeout': 3.0,
            'popup_auto_close': 10.0,
            'show_main_window_on_start': False
        }

        # ログ設定
        self._setup_logging()

        # 多重起動防止チェック
        self.single_instance_manager = SingleInstanceManager("CCTranslation")
        print(f"多重起動防止チェック開始...")
        if self.single_instance_manager.check_and_exit_if_running():
            print(f"既存インスタンス検出 - 終了します")
            sys.exit(1)  # 既存インスタンスが存在する場合は終了
        print(f"多重起動防止チェック完了 - 続行します")

        # ロックファイル作成確認
        if hasattr(self.single_instance_manager, 'acquire_lock'):
            if self.single_instance_manager.acquire_lock():
                print(f"ロックファイル作成成功: {self.single_instance_manager.lock_file_path}")
            else:
                print(f"ロックファイル作成失敗")
                sys.exit(1)

        print("CCTranslation アプリケーション初期化開始")

    def _setup_logging(self):
        """ログ設定"""
        try:
            # ログディレクトリ作成
            log_dir = project_root / "logs"
            log_dir.mkdir(exist_ok=True)

            # ログファイル設定
            log_file = log_dir / f"cctranslation_{time.strftime('%Y%m%d')}.log"

            # ログ設定
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )

            self.logger = logging.getLogger('CCTranslation')
            self.logger.info("ログシステム初期化完了")

        except Exception as e:
            print(f"ログ設定エラー: {e}")
            # フォールバック: 基本的なログ設定
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('CCTranslation')

    def initialize_components(self):
        """全コンポーネントの初期化"""
        try:
            self.logger.info("コンポーネント初期化開始")

            # 1. 設定と言語管理の初期化
            self._initialize_managers()

            # 2. コアコンポーネントの初期化
            self._initialize_core_components()

            # 3. UIコンポーネントの初期化
            self._initialize_ui_components()

            # 4. システムトレイの初期化
            self._initialize_system_tray()

            # 5. 設定の読み込み
            self._load_settings()

            # 6. コンポーネント間の統合
            self._integrate_components()

            self.logger.info("コンポーネント初期化完了")

        except Exception as e:
            self.logger.error(f"コンポーネント初期化エラー: {e}")
            raise CCTranslationException(f"アプリケーション初期化に失敗しました: {e}")

    def _initialize_managers(self):
        """管理オブジェクトの初期化"""
        try:
            self.config_manager = ConfigManager()
            self.language_manager = LanguageManager()
            self.logger.info("管理オブジェクト初期化完了")
        except Exception as e:
            self.logger.error(f"管理オブジェクト初期化エラー: {e}")
            raise

    def _initialize_core_components(self):
        """コアコンポーネントの初期化"""
        try:
            # ホットキー管理
            self.hotkey_manager = HotkeyManager(self._on_double_copy_detected)

            # クリップボード管理
            self.clipboard_manager = ClipboardManager()

            # 翻訳管理
            self.translation_manager = TranslationManager()
            self.translation_manager.set_status_callback(self._on_translation_status_changed)
            self.translation_manager.set_completion_callback(self._on_translation_completed)

            self.logger.info("コアコンポーネント初期化完了")
        except Exception as e:
            self.logger.error(f"コアコンポーネント初期化エラー: {e}")
            raise

    def _initialize_ui_components(self):
        """UIコンポーネントの初期化"""
        try:
            # ポップアップウィンドウ
            self.popup_window = PopupWindow(self.config_manager, self.language_manager)
            self.popup_window.set_callbacks(
                on_translation_complete=self._on_popup_translation_complete,
                on_popup_closed=self._on_popup_closed
            )

            # メインウィンドウ（ポップアップ用に作成、非表示）
            self.main_window = MainWindow(self.config_manager, self.language_manager)
            # メインウィンドウは非表示のまま（ポップアップ用のみ）

            # ポップアップウィンドウにメインウィンドウの参照を設定
            if self.popup_window:
                self.popup_window.set_root(self.main_window.root)

            self.logger.info("UIコンポーネント初期化完了")
        except Exception as e:
            self.logger.error(f"UIコンポーネント初期化エラー: {e}")
            raise

    def _initialize_system_tray(self):
        """システムトレイの初期化"""
        try:
            self.system_tray = SystemTrayApp()
            self.system_tray.popup_window = self.popup_window
            if self.main_window:
                self.system_tray.main_window = self.main_window
                # システムトレイに既存のメインウィンドウインスタンスを設定
                self.system_tray.set_main_window_instance(self.main_window)

            # メインウィンドウ表示コールバックを設定
            self.system_tray.set_callbacks(
                on_show_main_window=self.show_main_window
            )

            self.logger.info("システムトレイ初期化完了")
        except Exception as e:
            self.logger.error(f"システムトレイ初期化エラー: {e}")
            raise

    def _load_settings(self):
        """設定の読み込み"""
        try:
            if self.config_manager:
                # 設定ファイルから読み込み
                self.settings['source_language'] = self.config_manager.get('translation', 'source_language', 'auto')
                self.settings['target_language'] = self.config_manager.get('translation', 'target_language', 'ja')
                self.settings['double_copy_interval'] = self.config_manager.get_float('hotkey', 'double_copy_interval', 0.5)
                self.settings['translation_timeout'] = self.config_manager.get_float('translation', 'timeout', 3.0)
                self.settings['popup_auto_close'] = self.config_manager.get_float('ui', 'popup_auto_close', 10.0)
                self.settings['show_main_window_on_start'] = self.config_manager.get_boolean('ui', 'show_main_window_on_start', False)

                self.logger.info("設定読み込み完了")
        except Exception as e:
            self.logger.warning(f"設定読み込みエラー（デフォルト値を使用）: {e}")

    def _integrate_components(self):
        """コンポーネント間の統合"""
        try:
            # ホットキー管理の設定
            if self.hotkey_manager:
                self.hotkey_manager.double_copy_detector.set_interval(self.settings['double_copy_interval'])

            # 翻訳管理の設定
            if self.translation_manager:
                self.translation_manager.timeout_seconds = self.settings['translation_timeout']

            # ポップアップウィンドウの設定
            if self.popup_window:
                self.popup_window.config.auto_close_delay = self.settings['popup_auto_close']

            self.logger.info("コンポーネント統合完了")
        except Exception as e:
            self.logger.error(f"コンポーネント統合エラー: {e}")
            raise

    def start_application(self):
        """アプリケーションを開始"""
        try:
            if self.is_running:
                self.logger.warning("アプリケーションは既に実行中です")
                return

            self.logger.info("アプリケーション開始")

            # コンポーネント初期化
            self.initialize_components()

            # ホットキー監視開始
            if self.hotkey_manager:
                self.hotkey_manager.start_monitoring()
                self.logger.info("ホットキー監視開始")

            # システムトレイ開始
            if self.system_tray:
                self.system_tray.start_application()
                self.logger.info("システムトレイ開始")

            # 初回通知
            if self.system_tray:
                self.system_tray.system_tray.show_notification(
                    "CCTranslation",
                    "翻訳ツールが開始されました。Ctrl+Cを2回押して翻訳を開始してください。",
                    3.0
                )

            # メインウィンドウ表示（設定により）
            if self.settings['show_main_window_on_start']:
                self.show_main_window()

            self.is_running = True
            self.logger.info("アプリケーション開始完了")

        except Exception as e:
            self.logger.error(f"アプリケーション開始エラー: {e}")
            self.stop_application()
            raise CCTranslationException(f"アプリケーションの開始に失敗しました: {e}")

    def stop_application(self):
        """アプリケーションを停止"""
        try:
            if not self.is_running:
                return

            self.logger.info("アプリケーション停止開始")

            # 翻訳中の場合は停止
            if self.is_translating and self.translation_manager:
                self.translation_manager.cancel_translation()

            # ホットキー監視停止
            if self.hotkey_manager:
                self.hotkey_manager.stop_monitoring()
                self.logger.info("ホットキー監視停止")

            # ポップアップウィンドウ非表示
            if self.popup_window:
                self.popup_window.hide_popup()

            # メインウィンドウの完全終了
            if self.main_window:
                self.main_window.root.quit()
                self.main_window.root.destroy()
                self.logger.info("メインウィンドウ終了")

            # システムトレイ停止
            if self.system_tray:
                self.system_tray.exit_application()
                self.logger.info("システムトレイ停止")

            # 設定保存
            self._save_settings()

            # 単一インスタンスロック解放
            if hasattr(self, 'single_instance_manager'):
                self.single_instance_manager.release_lock()

            self.is_running = False
            self.logger.info("アプリケーション停止完了")

            # プロセスを強制終了
            import os
            os._exit(0)

        except Exception as e:
            self.logger.error(f"アプリケーション停止エラー: {e}")
            # エラーが発生した場合も強制終了
            import os
            os._exit(1)

    def _save_settings(self):
        """設定の保存"""
        try:
            if self.config_manager:
                self.config_manager.set('translation', 'source_language', self.settings['source_language'])
                self.config_manager.set('translation', 'target_language', self.settings['target_language'])
                self.config_manager.set('hotkey', 'double_copy_interval', str(self.settings['double_copy_interval']))
                self.config_manager.set('translation', 'timeout', str(self.settings['translation_timeout']))
                self.config_manager.set('ui', 'popup_auto_close', str(self.settings['popup_auto_close']))
                self.config_manager.set('ui', 'show_main_window_on_start', str(self.settings['show_main_window_on_start']))

                self.logger.info("設定保存完了")
        except Exception as e:
            self.logger.warning(f"設定保存エラー: {e}")

    def show_main_window(self):
        """メインウィンドウを表示"""
        try:
            if self.main_window and self.main_window.root:
                self.main_window.root.deiconify()  # ウィンドウを表示
                self.main_window.root.lift()       # ウィンドウを前面に
                self.main_window.root.focus_force()  # フォーカスを取得
                self.logger.info("メインウィンドウ表示")
            else:
                self.logger.warning("メインウィンドウが初期化されていません")

        except Exception as e:
            self.logger.error(f"メインウィンドウ表示エラー: {e}")

    # イベントハンドラー

    def _on_double_copy_detected(self):
        """ダブルコピー検出時のイベントハンドラー"""
        try:
            self.logger.info("ダブルコピー検出")

            if self.is_translating:
                self.logger.warning("翻訳処理中です")
                return

            # クリップボードからテキストを取得
            text = self.clipboard_manager.get_text_for_translation()
            if not text:
                self.logger.info("クリップボードが空です")
                return

            self.logger.info(f"翻訳開始: {text[:50]}...")

            # 翻訳処理開始
            self._start_translation(text)

        except Exception as e:
            self.logger.error(f"ダブルコピー検出処理エラー: {e}")
            self._show_error_popup(f"翻訳開始エラー: {e}")

    def _start_translation(self, text: str):
        """翻訳処理開始"""
        try:
            self.is_translating = True

            # システムトレイ通知のみ（ポップアップは翻訳完了時のみ表示）
            if self.system_tray:
                self.system_tray.system_tray.show_notification(
                    "翻訳開始",
                    f"翻訳中: {text[:30]}...",
                    1.0
                )

            # 非同期翻訳実行
            self.translation_manager.translate_async(
                text,
                self.settings['target_language'],
                self.settings['source_language']
            )

        except Exception as e:
            self.logger.error(f"翻訳開始エラー: {e}")
            self.is_translating = False
            self._show_error_popup(f"翻訳開始エラー: {e}")

    def _on_translation_status_changed(self, status: TranslationStatus, result: Optional[TranslationResult]):
        """翻訳状態変更時のイベントハンドラー"""
        try:
            status_messages = {
                TranslationStatus.IDLE: "待機中",
                TranslationStatus.TRANSLATING: "翻訳中...",
                TranslationStatus.COMPLETED: "翻訳完了",
                TranslationStatus.TIMEOUT: "タイムアウト",
                TranslationStatus.ERROR: "エラー"
            }

            message = status_messages.get(status, "不明")
            self.logger.info(f"翻訳状態変更: {message}")

            # ログ出力のみ（ポップアップは翻訳完了時のみ表示）

        except Exception as e:
            self.logger.error(f"翻訳状態変更処理エラー: {e}")

    def _on_translation_completed(self, result: TranslationResult):
        """翻訳完了時のイベントハンドラー"""
        try:
            self.is_translating = False

            if result.status == TranslationStatus.COMPLETED:
                self.logger.info(f"翻訳完了: {result.translated_text[:50]}...")

                # 翻訳結果ポップアップ表示（メインスレッドで実行）
                if self.popup_window:
                    try:
                        self.popup_window.root.after(0, lambda: self.popup_window.show_translation_popup(result))
                    except Exception as e:
                        self.logger.warning(f"翻訳結果ポップアップ表示エラー: {e}")

                # システムトレイ通知
                if self.system_tray:
                    self.system_tray.system_tray.show_notification(
                        "翻訳完了",
                        f"翻訳結果: {result.translated_text[:30]}...",
                        2.0
                    )

            elif result.status == TranslationStatus.TIMEOUT:
                self.logger.warning("翻訳タイムアウト")
                self._show_error_popup("翻訳がタイムアウトしました。ネットワーク接続を確認してください。")

            elif result.status == TranslationStatus.ERROR:
                self.logger.error(f"翻訳エラー: {result.error_message}")
                self._show_error_popup(f"翻訳エラー: {result.error_message}")

        except Exception as e:
            self.logger.error(f"翻訳完了処理エラー: {e}")
            self.is_translating = False

    def _on_popup_translation_complete(self, result: TranslationResult):
        """ポップアップ翻訳完了時のイベントハンドラー"""
        try:
            self.logger.info("ポップアップ翻訳完了")
            # 必要に応じて追加の処理

        except Exception as e:
            self.logger.error(f"ポップアップ翻訳完了処理エラー: {e}")

    def _on_popup_closed(self):
        """ポップアップ閉じる時のイベントハンドラー"""
        try:
            self.logger.info("ポップアップ閉じる")
            # 必要に応じて追加の処理

        except Exception as e:
            self.logger.error(f"ポップアップ閉じる処理エラー: {e}")

    def _show_error_popup(self, error_message: str):
        """エラーポップアップ表示"""
        try:
            if self.popup_window:
                # Tkinterのメインループが動作している場合のみ表示
                try:
                    self.popup_window.root.after(0, lambda: self.popup_window.show_error_popup(error_message))
                except Exception as e:
                    self.logger.warning(f"エラーポップアップ表示エラー: {e}")

            # システムトレイ通知
            if self.system_tray:
                self.system_tray.system_tray.show_notification(
                    "エラー",
                    error_message,
                    3.0
                )

        except Exception as e:
            self.logger.error(f"エラーポップアップ表示エラー: {e}")

    def get_status(self) -> Dict[str, Any]:
        """アプリケーション状態を取得"""
        return {
            'is_running': self.is_running,
            'is_translating': self.is_translating,
            'settings': self.settings,
            'components': {
                'config_manager': self.config_manager is not None,
                'language_manager': self.language_manager is not None,
                'hotkey_manager': self.hotkey_manager is not None,
                'clipboard_manager': self.clipboard_manager is not None,
                'translation_manager': self.translation_manager is not None,
                'popup_window': self.popup_window is not None,
                'main_window': self.main_window is not None,
                'system_tray': self.system_tray is not None
            }
        }


def main():
    """メイン関数"""
    app = None
    try:
        print("CCTranslation 起動中...")

        # アプリケーション作成
        app = CCTranslationApp()

        # アプリケーション開始
        app.start_application()

        print("CCTranslation が正常に開始されました。")
        print("システムトレイアイコンを確認してください。")
        print("終了するには、システムトレイメニューから「終了」を選択してください。")

        # メインループ
        try:
            # Tkinterのメインループを開始
            if app.main_window and app.main_window.root:
                app.main_window.root.mainloop()
            else:
                # メインウィンドウがない場合は通常のループ
                while app.is_running:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nキーボード割り込みで終了します")

    except Exception as e:
        print(f"アプリケーション実行エラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if app:
            app.stop_application()
        print("CCTranslation を終了しました。")


if __name__ == "__main__":
    main()