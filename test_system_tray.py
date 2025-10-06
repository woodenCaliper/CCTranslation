"""
システムトレイ統合のテスト

SystemTrayManagerとSystemTrayAppの動作確認を行う
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import time
import threading

from ui.system_tray import SystemTrayManager, SystemTrayApp
from data.config import ConfigManager
from data.language import LanguageManager


class SystemTrayTestApp:
    """システムトレイテストアプリケーション"""

    def __init__(self):
        self.test_results = []
        self.system_tray = None
        self.app = None

    def test_system_tray_creation(self):
        """システムトレイ作成テスト"""
        print("=== システムトレイ作成テスト ===")

        try:
            # 設定と言語管理の初期化
            config_manager = ConfigManager()
            language_manager = LanguageManager()

            # システムトレイ管理の作成
            self.system_tray = SystemTrayManager(config_manager, language_manager)

            # 基本プロパティをチェック
            success = (
                self.system_tray.config_manager is not None and
                self.system_tray.language_manager is not None and
                self.system_tray.icon_image is not None and
                not self.system_tray.is_running
            )

            print(f"   システムトレイ作成: {'OK' if success else 'NG'}")
            print(f"   設定マネージャー: {'OK' if self.system_tray.config_manager else 'NG'}")
            print(f"   言語マネージャー: {'OK' if self.system_tray.language_manager else 'NG'}")
            print(f"   アイコン画像: {'OK' if self.system_tray.icon_image else 'NG'}")
            print(f"   実行状態: {self.system_tray.is_running}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("システムトレイ作成", success))

        except Exception as e:
            print(f"NG システムトレイ作成テストでエラー: {e}")
            self.test_results.append(("システムトレイ作成テスト", False))

    def test_icon_creation(self):
        """アイコン作成テスト"""
        print("\n=== アイコン作成テスト ===")

        try:
            if not self.system_tray:
                print("   システムトレイが作成されていません")
                self.test_results.append(("アイコン作成", False))
                return

            # アイコン画像の確認
            icon_exists = self.system_tray.icon_image is not None
            icon_size = self.system_tray.icon_image.size if self.system_tray.icon_image else None

            print(f"   アイコン存在: {icon_exists}")
            print(f"   アイコンサイズ: {icon_size}")

            success = icon_exists and icon_size is not None
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("アイコン作成", success))

        except Exception as e:
            print(f"NG アイコン作成テストでエラー: {e}")
            self.test_results.append(("アイコン作成テスト", False))

    def test_menu_creation(self):
        """メニュー作成テスト"""
        print("\n=== メニュー作成テスト ===")

        try:
            if not self.system_tray:
                print("   システムトレイが作成されていません")
                self.test_results.append(("メニュー作成", False))
                return

            # メニューの作成
            menu = self.system_tray.create_menu()

            # メニューの確認
            menu_exists = menu is not None

            print(f"   メニュー存在: {menu_exists}")
            print(f"   メニュー項目数: {len(menu._items) if menu else 0}")

            success = menu_exists
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("メニュー作成", success))

        except Exception as e:
            print(f"NG メニュー作成テストでエラー: {e}")
            self.test_results.append(("メニュー作成テスト", False))

    def test_callback_functionality(self):
        """コールバック機能テスト"""
        print("\n=== コールバック機能テスト ===")

        try:
            if not self.system_tray:
                print("   システムトレイが作成されていません")
                self.test_results.append(("コールバック機能", False))
                return

            # コールバック用の変数
            show_main_window_called = False
            exit_app_called = False

            def on_show_main_window():
                nonlocal show_main_window_called
                show_main_window_called = True
                print("   メインウィンドウ表示コールバック")

            def on_exit_app():
                nonlocal exit_app_called
                exit_app_called = True
                print("   アプリ終了コールバック")

            # コールバックを設定
            self.system_tray.set_callbacks(
                on_show_main_window=on_show_main_window,
                on_exit_app=on_exit_app
            )

            # コールバックを直接呼び出し
            self.system_tray._show_main_window()
            self.system_tray._exit_application()

            print(f"   メインウィンドウ表示コールバック: {show_main_window_called}")
            print(f"   アプリ終了コールバック: {exit_app_called}")

            success = show_main_window_called and exit_app_called
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("コールバック機能", success))

        except Exception as e:
            print(f"NG コールバック機能テストでエラー: {e}")
            self.test_results.append(("コールバック機能テスト", False))

    def test_system_tray_app(self):
        """システムトレイアプリケーションテスト"""
        print("\n=== システムトレイアプリケーションテスト ===")

        try:
            # システムトレイアプリケーションの作成
            self.app = SystemTrayApp()

            # 基本プロパティをチェック
            success = (
                self.app.config_manager is not None and
                self.app.language_manager is not None and
                self.app.system_tray is not None and
                not self.app.is_running
            )

            print(f"   アプリケーション作成: {'OK' if success else 'NG'}")
            print(f"   設定マネージャー: {'OK' if self.app.config_manager else 'NG'}")
            print(f"   言語マネージャー: {'OK' if self.app.language_manager else 'NG'}")
            print(f"   システムトレイ: {'OK' if self.app.system_tray else 'NG'}")
            print(f"   実行状態: {self.app.is_running}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("システムトレイアプリケーション", success))

        except Exception as e:
            print(f"NG システムトレイアプリケーションテストでエラー: {e}")
            self.test_results.append(("システムトレイアプリケーションテスト", False))

    def test_ui_components_initialization(self):
        """UIコンポーネント初期化テスト"""
        print("\n=== UIコンポーネント初期化テスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("UIコンポーネント初期化", False))
                return

            # UIコンポーネントの初期化
            self.app.initialize_ui_components()

            # コンポーネントの確認
            popup_exists = self.app.popup_window is not None
            main_window_exists = self.app.main_window is not None

            print(f"   ポップアップウィンドウ: {'OK' if popup_exists else 'NG'}")
            print(f"   メインウィンドウ: {'OK' if main_window_exists else 'NG'}")

            success = popup_exists
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("UIコンポーネント初期化", success))

        except Exception as e:
            print(f"NG UIコンポーネント初期化テストでエラー: {e}")
            self.test_results.append(("UIコンポーネント初期化テスト", False))

    def test_status_management(self):
        """状態管理テスト"""
        print("\n=== 状態管理テスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("状態管理", False))
                return

            # 初期状態確認
            initial_status = self.app.get_status()

            print(f"   初期状態: {initial_status}")

            # アプリケーション開始（短時間）
            self.app.start_application()
            time.sleep(0.5)  # 短時間待機

            running_status = self.app.get_status()

            # アプリケーション終了
            self.app.exit_application()

            final_status = self.app.get_status()

            print(f"   実行中状態: {running_status}")
            print(f"   終了後状態: {final_status}")

            success = (
                not initial_status['is_running'] and
                running_status['is_running'] and
                not final_status['is_running']
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("状態管理", success))

        except Exception as e:
            print(f"NG 状態管理テストでエラー: {e}")
            self.test_results.append(("状態管理テスト", False))

    def run_all_tests(self):
        """全テストを実行"""
        print("======================================================================")
        print("システムトレイ統合 テスト開始")
        print("======================================================================")

        # 各テストを実行
        self.test_system_tray_creation()
        self.test_icon_creation()
        self.test_menu_creation()
        self.test_callback_functionality()
        self.test_system_tray_app()
        self.test_ui_components_initialization()
        self.test_status_management()

        # 結果を表示
        print("\n======================================================================")
        print("テスト結果")
        print("======================================================================")

        passed = 0
        total = len(self.test_results)

        for test_name, result in self.test_results:
            status = "OK" if result else "NG"
            print(f"{test_name}: {status}")
            if result:
                passed += 1

        print(f"\n合計: {passed}/{total} テストが成功")

        if passed == total:
            print("全てのテストが成功しました！")
        else:
            print("一部のテストが失敗しました。")

        print("======================================================================")

        # クリーンアップ
        if self.app:
            self.app.exit_application()

    def run_interactive_test(self):
        """インタラクティブテスト（実際のシステムトレイ表示）"""
        print("\n=== インタラクティブテスト ===")
        print("システムトレイが表示されます。手動でテストしてください。")
        print("テスト完了後、システムトレイメニューから「終了」を選択してください。")

        try:
            if not self.app:
                print("アプリケーションが作成されていません")
                return

            # アプリケーションを開始
            self.app.start_application()

            print("システムトレイアイコンを確認してください。")
            print("右クリックでメニューが表示されることを確認してください。")

            # メインループ
            try:
                while self.app.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nキーボード割り込みで終了します")
                self.app.exit_application()

        except Exception as e:
            print(f"インタラクティブテストエラー: {e}")
        finally:
            if self.app:
                self.app.exit_application()


def main():
    """メイン関数"""
    try:
        app = SystemTrayTestApp()

        # 自動テストを実行
        app.run_all_tests()

        # インタラクティブテストの実行を確認
        print("\nインタラクティブテストを実行しますか？ (y/n): ", end="")
        response = input().strip().lower()

        if response == 'y':
            app = SystemTrayTestApp()
            app.test_system_tray_app()
            app.test_ui_components_initialization()
            app.run_interactive_test()

    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
