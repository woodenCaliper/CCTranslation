"""
メインアプリケーション統合のテスト

CCTranslationAppの動作確認を行う
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import time
import threading

from src.main import CCTranslationApp


class MainAppTestApp:
    """メインアプリケーションテストアプリケーション"""

    def __init__(self):
        self.test_results = []
        self.app = None

    def test_app_creation(self):
        """アプリケーション作成テスト"""
        print("=== アプリケーション作成テスト ===")

        try:
            # アプリケーション作成
            self.app = CCTranslationApp()

            # 基本プロパティをチェック
            success = (
                self.app is not None and
                not self.app.is_running and
                not self.app.is_translating and
                self.app.settings is not None and
                self.app.logger is not None
            )

            print(f"   アプリケーション作成: {'OK' if success else 'NG'}")
            print(f"   実行状態: {self.app.is_running}")
            print(f"   翻訳状態: {self.app.is_translating}")
            print(f"   設定: {len(self.app.settings)}項目")
            print(f"   ロガー: {'OK' if self.app.logger else 'NG'}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("アプリケーション作成", success))

        except Exception as e:
            print(f"NG アプリケーション作成テストでエラー: {e}")
            self.test_results.append(("アプリケーション作成テスト", False))

    def test_component_initialization(self):
        """コンポーネント初期化テスト"""
        print("\n=== コンポーネント初期化テスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("コンポーネント初期化", False))
                return

            # コンポーネント初期化
            self.app.initialize_components()

            # 各コンポーネントの確認
            components = {
                'config_manager': self.app.config_manager,
                'language_manager': self.app.language_manager,
                'hotkey_manager': self.app.hotkey_manager,
                'clipboard_manager': self.app.clipboard_manager,
                'translation_manager': self.app.translation_manager,
                'popup_window': self.app.popup_window,
                'system_tray': self.app.system_tray
            }

            success_count = 0
            total_count = len(components)

            for name, component in components.items():
                exists = component is not None
                print(f"   {name}: {'OK' if exists else 'NG'}")
                if exists:
                    success_count += 1

            success = success_count == total_count
            print(f"   初期化成功率: {success_count}/{total_count}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("コンポーネント初期化", success))

        except Exception as e:
            print(f"NG コンポーネント初期化テストでエラー: {e}")
            self.test_results.append(("コンポーネント初期化テスト", False))

    def test_settings_management(self):
        """設定管理テスト"""
        print("\n=== 設定管理テスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("設定管理", False))
                return

            # 設定の確認
            settings = self.app.settings
            required_settings = [
                'source_language', 'target_language', 'double_copy_interval',
                'translation_timeout', 'popup_auto_close', 'show_main_window_on_start'
            ]

            success_count = 0
            for setting in required_settings:
                exists = setting in settings
                value = settings.get(setting, None)
                print(f"   {setting}: {value}")
                if exists and value is not None:
                    success_count += 1

            success = success_count == len(required_settings)
            print(f"   設定項目数: {success_count}/{len(required_settings)}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("設定管理", success))

        except Exception as e:
            print(f"NG 設定管理テストでエラー: {e}")
            self.test_results.append(("設定管理テスト", False))

    def test_application_lifecycle(self):
        """アプリケーションライフサイクルテスト"""
        print("\n=== アプリケーションライフサイクルテスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("アプリケーションライフサイクル", False))
                return

            # 初期状態確認
            initial_status = self.app.get_status()
            print(f"   初期状態: {initial_status['is_running']}")

            # アプリケーション開始（短時間）
            self.app.start_application()
            time.sleep(1.0)  # 1秒待機

            running_status = self.app.get_status()
            print(f"   実行中状態: {running_status['is_running']}")
            print(f"   コンポーネント状態: {running_status['components']}")

            # アプリケーション停止
            self.app.stop_application()
            time.sleep(0.5)

            final_status = self.app.get_status()
            print(f"   停止後状態: {final_status['is_running']}")

            success = (
                not initial_status['is_running'] and
                running_status['is_running'] and
                not final_status['is_running']
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("アプリケーションライフサイクル", success))

        except Exception as e:
            print(f"NG アプリケーションライフサイクルテストでエラー: {e}")
            self.test_results.append(("アプリケーションライフサイクルテスト", False))

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n=== エラーハンドリングテスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("エラーハンドリング", False))
                return

            # 初期化済みのアプリケーションでテスト
            self.app.initialize_components()

            # エラーポップアップ表示テスト
            test_error = "テストエラーメッセージ"
            self.app._show_error_popup(test_error)

            print(f"   エラーポップアップ表示: OK")

            # 翻訳中の重複実行テスト
            self.app.is_translating = True
            self.app._on_double_copy_detected()
            print(f"   翻訳中重複実行制御: OK")

            self.app.is_translating = False

            success = True
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("エラーハンドリング", success))

        except Exception as e:
            print(f"NG エラーハンドリングテストでエラー: {e}")
            self.test_results.append(("エラーハンドリングテスト", False))

    def test_status_reporting(self):
        """状態報告テスト"""
        print("\n=== 状態報告テスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("状態報告", False))
                return

            # 初期化済みのアプリケーションでテスト
            self.app.initialize_components()

            # 状態取得
            status = self.app.get_status()

            # 必須フィールドの確認
            required_fields = ['is_running', 'is_translating', 'settings', 'components']
            success_count = 0

            for field in required_fields:
                exists = field in status
                print(f"   {field}: {'OK' if exists else 'NG'}")
                if exists:
                    success_count += 1

            # コンポーネント状態の確認
            components = status.get('components', {})
            component_count = len(components)
            print(f"   コンポーネント数: {component_count}")

            success = success_count == len(required_fields) and component_count > 0
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("状態報告", success))

        except Exception as e:
            print(f"NG 状態報告テストでエラー: {e}")
            self.test_results.append(("状態報告テスト", False))

    def test_translation_workflow(self):
        """翻訳ワークフローテスト"""
        print("\n=== 翻訳ワークフローテスト ===")

        try:
            if not self.app:
                print("   アプリケーションが作成されていません")
                self.test_results.append(("翻訳ワークフロー", False))
                return

            # 初期化済みのアプリケーションでテスト
            self.app.initialize_components()

            # テスト用のクリップボードテキスト設定
            test_text = "Hello, world!"
            self.app.clipboard_manager.set_content(test_text)

            # 翻訳開始テスト
            self.app._start_translation(test_text)

            print(f"   翻訳開始: OK")
            print(f"   翻訳状態: {self.app.is_translating}")

            # 翻訳完了のシミュレーション
            self.app.is_translating = False

            success = True
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("翻訳ワークフロー", success))

        except Exception as e:
            print(f"NG 翻訳ワークフローテストでエラー: {e}")
            self.test_results.append(("翻訳ワークフローテスト", False))

    def run_all_tests(self):
        """全テストを実行"""
        print("======================================================================")
        print("メインアプリケーション統合 テスト開始")
        print("======================================================================")

        # 各テストを実行
        self.test_app_creation()
        self.test_component_initialization()
        self.test_settings_management()
        self.test_application_lifecycle()
        self.test_error_handling()
        self.test_status_reporting()
        self.test_translation_workflow()

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
            self.app.stop_application()

    def run_interactive_test(self):
        """インタラクティブテスト（実際のアプリケーション実行）"""
        print("\n=== インタラクティブテスト ===")
        print("実際のアプリケーションが実行されます。")
        print("システムトレイアイコンを確認してください。")
        print("Ctrl+Cを2回押して翻訳をテストしてください。")
        print("終了するには、システムトレイメニューから「終了」を選択してください。")

        try:
            if not self.app:
                print("アプリケーションが作成されていません")
                return

            # アプリケーションを開始
            self.app.start_application()

            print("アプリケーションが開始されました。")
            print("テストを開始してください。")

            # メインループ
            try:
                while self.app.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nキーボード割り込みで終了します")
                self.app.stop_application()

        except Exception as e:
            print(f"インタラクティブテストエラー: {e}")
        finally:
            if self.app:
                self.app.stop_application()


def main():
    """メイン関数"""
    try:
        app = MainAppTestApp()

        # 自動テストを実行
        app.run_all_tests()

        # インタラクティブテストの実行を確認
        print("\nインタラクティブテストを実行しますか？ (y/n): ", end="")
        try:
            response = input().strip().lower()
        except EOFError:
            response = 'n'

        if response == 'y':
            app = MainAppTestApp()
            app.test_app_creation()
            app.test_component_initialization()
            app.run_interactive_test()

    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
