"""
ポップアップ表示システムのテスト

PopupWindowの動作確認を行う
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from tkinter import messagebox
import threading
import time

from ui.popup_window import PopupWindow, PopupState
from data.config import ConfigManager
from data.language import LanguageManager
from core.translation_manager import TranslationResult, TranslationStatus


class PopupWindowTestApp:
    """ポップアップウィンドウテストアプリケーション"""

    def __init__(self):
        self.test_results = []
        self.popup = None
        self.root = None

    def test_popup_creation(self):
        """ポップアップ作成テスト"""
        print("=== ポップアップ作成テスト ===")

        try:
            # 設定と言語管理の初期化
            config_manager = ConfigManager()
            language_manager = LanguageManager()

            # ポップアップウィンドウの作成
            self.popup = PopupWindow(config_manager, language_manager)

            # 基本プロパティをチェック
            success = (
                self.popup.translation_manager is not None and
                self.popup.clipboard_manager is not None and
                self.popup.state == PopupState.HIDDEN and
                self.popup.window is None
            )

            print(f"   ポップアップ作成: {'OK' if success else 'NG'}")
            print(f"   翻訳マネージャー: {'OK' if self.popup.translation_manager else 'NG'}")
            print(f"   クリップボードマネージャー: {'OK' if self.popup.clipboard_manager else 'NG'}")
            print(f"   初期状態: {self.popup.state.value}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("ポップアップ作成", success))

        except Exception as e:
            print(f"NG ポップアップ作成テストでエラー: {e}")
            self.test_results.append(("ポップアップ作成テスト", False))

    def test_status_popup(self):
        """ステータスポップアップテスト"""
        print("\n=== ステータスポップアップテスト ===")

        try:
            if not self.popup:
                print("   ポップアップが作成されていません")
                self.test_results.append(("ステータスポップアップ", False))
                return

            # ステータスポップアップを表示
            self.popup.show_status_popup("翻訳中...")

            # 状態をチェック
            state_ok = (self.popup.state == PopupState.STATUS_DISPLAY)
            window_ok = (self.popup.window is not None)
            visible_ok = self.popup.is_visible()

            print(f"   ステータス表示: {self.popup.state.value}")
            print(f"   ウィンドウ存在: {window_ok}")
            print(f"   表示状態: {visible_ok}")

            success = state_ok and window_ok and visible_ok
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("ステータスポップアップ", success))

            # 少し待ってから非表示
            time.sleep(1)
            self.popup.hide_popup()

        except Exception as e:
            print(f"NG ステータスポップアップテストでエラー: {e}")
            self.test_results.append(("ステータスポップアップテスト", False))

    def test_translation_popup(self):
        """翻訳結果ポップアップテスト"""
        print("\n=== 翻訳結果ポップアップテスト ===")

        try:
            if not self.popup:
                print("   ポップアップが作成されていません")
                self.test_results.append(("翻訳結果ポップアップ", False))
                return

            # テスト用の翻訳結果を作成
            result = TranslationResult(
                source_text="Hello, world!",
                translated_text="こんにちは、世界！",
                source_language="en",
                target_language="ja",
                status=TranslationStatus.COMPLETED,
                timestamp=time.time(),
                processing_time=1.5
            )

            # 翻訳結果ポップアップを表示
            self.popup.show_translation_popup(result)

            # 状態をチェック
            state_ok = (self.popup.state == PopupState.TRANSLATION_DISPLAY)
            window_ok = (self.popup.window is not None)
            visible_ok = self.popup.is_visible()
            result_ok = (self.popup.current_translation_result == result)

            print(f"   翻訳結果表示: {self.popup.state.value}")
            print(f"   ウィンドウ存在: {window_ok}")
            print(f"   表示状態: {visible_ok}")
            print(f"   結果保存: {result_ok}")

            success = state_ok and window_ok and visible_ok and result_ok
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("翻訳結果ポップアップ", success))

            # 少し待ってから非表示
            time.sleep(1)
            self.popup.hide_popup()

        except Exception as e:
            print(f"NG 翻訳結果ポップアップテストでエラー: {e}")
            self.test_results.append(("翻訳結果ポップアップテスト", False))

    def test_error_popup(self):
        """エラーポップアップテスト"""
        print("\n=== エラーポップアップテスト ===")

        try:
            if not self.popup:
                print("   ポップアップが作成されていません")
                self.test_results.append(("エラーポップアップ", False))
                return

            # エラーポップアップを表示
            error_message = "翻訳エラー: ネットワーク接続に失敗しました"
            self.popup.show_error_popup(error_message)

            # 状態をチェック
            state_ok = (self.popup.state == PopupState.ERROR_DISPLAY)
            window_ok = (self.popup.window is not None)
            visible_ok = self.popup.is_visible()

            print(f"   エラー表示: {self.popup.state.value}")
            print(f"   ウィンドウ存在: {window_ok}")
            print(f"   表示状態: {visible_ok}")

            success = state_ok and window_ok and visible_ok
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("エラーポップアップ", success))

            # 少し待ってから非表示
            time.sleep(1)
            self.popup.hide_popup()

        except Exception as e:
            print(f"NG エラーポップアップテストでエラー: {e}")
            self.test_results.append(("エラーポップアップテスト", False))

    def test_popup_state_management(self):
        """ポップアップ状態管理テスト"""
        print("\n=== ポップアップ状態管理テスト ===")

        try:
            if not self.popup:
                print("   ポップアップが作成されていません")
                self.test_results.append(("状態管理", False))
                return

            # 初期状態確認
            initial_state = self.popup.get_current_state()
            initial_visible = self.popup.is_visible()

            print(f"   初期状態: {initial_state.value}")
            print(f"   初期表示状態: {initial_visible}")

            # ステータス表示
            self.popup.show_status_popup("テスト中...")
            status_state = self.popup.get_current_state()
            status_visible = self.popup.is_visible()

            # 翻訳結果表示
            result = TranslationResult(
                source_text="Test",
                translated_text="テスト",
                source_language="en",
                target_language="ja",
                status=TranslationStatus.COMPLETED,
                timestamp=time.time(),
                processing_time=0.5
            )
            self.popup.show_translation_popup(result)
            translation_state = self.popup.get_current_state()
            translation_visible = self.popup.is_visible()

            # 非表示
            self.popup.hide_popup()
            final_state = self.popup.get_current_state()
            final_visible = self.popup.is_visible()

            print(f"   ステータス状態: {status_state.value}")
            print(f"   翻訳状態: {translation_state.value}")
            print(f"   最終状態: {final_state.value}")
            print(f"   最終表示状態: {final_visible}")

            success = (
                initial_state == PopupState.HIDDEN and
                status_state == PopupState.STATUS_DISPLAY and
                translation_state == PopupState.TRANSLATION_DISPLAY and
                final_state == PopupState.HIDDEN and
                not final_visible
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("状態管理", success))

        except Exception as e:
            print(f"NG 状態管理テストでエラー: {e}")
            self.test_results.append(("状態管理テスト", False))

    def test_clipboard_integration(self):
        """クリップボード統合テスト"""
        print("\n=== クリップボード統合テスト ===")

        try:
            if not self.popup:
                print("   ポップアップが作成されていません")
                self.test_results.append(("クリップボード統合", False))
                return

            # テスト用の翻訳結果を作成
            result = TranslationResult(
                source_text="Copy test",
                translated_text="コピーテスト",
                source_language="en",
                target_language="ja",
                status=TranslationStatus.COMPLETED,
                timestamp=time.time(),
                processing_time=0.3
            )

            # 翻訳結果ポップアップを表示
            self.popup.show_translation_popup(result)

            # クリップボードコピーをテスト
            self.popup._copy_result(result.translated_text)

            # クリップボードの内容を確認
            clipboard_content = self.popup.clipboard_manager.get_text_for_translation()

            print(f"   コピーしたテキスト: {result.translated_text}")
            print(f"   クリップボード内容: {clipboard_content}")

            success = (clipboard_content == result.translated_text)
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("クリップボード統合", success))

            # 非表示
            self.popup.hide_popup()

        except Exception as e:
            print(f"NG クリップボード統合テストでエラー: {e}")
            self.test_results.append(("クリップボード統合テスト", False))

    def test_callback_functionality(self):
        """コールバック機能テスト"""
        print("\n=== コールバック機能テスト ===")

        try:
            if not self.popup:
                print("   ポップアップが作成されていません")
                self.test_results.append(("コールバック機能", False))
                return

            # コールバック用の変数
            translation_complete_called = False
            popup_closed_called = False

            def on_translation_complete(result):
                nonlocal translation_complete_called
                translation_complete_called = True
                print(f"   翻訳完了コールバック: {result.translated_text[:20]}...")

            def on_popup_closed():
                nonlocal popup_closed_called
                popup_closed_called = True
                print("   ポップアップ閉じるコールバック")

            # コールバックを設定
            self.popup.set_callbacks(
                on_translation_complete=on_translation_complete,
                on_popup_closed=on_popup_closed
            )

            # 翻訳結果ポップアップを表示
            result = TranslationResult(
                source_text="Callback test",
                translated_text="コールバックテスト",
                source_language="en",
                target_language="ja",
                status=TranslationStatus.COMPLETED,
                timestamp=time.time(),
                processing_time=0.2
            )

            self.popup.show_translation_popup(result)

            # 非表示
            self.popup.hide_popup()

            print(f"   翻訳完了コールバック: {translation_complete_called}")
            print(f"   ポップアップ閉じるコールバック: {popup_closed_called}")

            success = translation_complete_called and popup_closed_called
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("コールバック機能", success))

        except Exception as e:
            print(f"NG コールバック機能テストでエラー: {e}")
            self.test_results.append(("コールバック機能テスト", False))

    def run_all_tests(self):
        """全テストを実行"""
        print("======================================================================")
        print("ポップアップ表示システム テスト開始")
        print("======================================================================")

        # 各テストを実行
        self.test_popup_creation()
        self.test_status_popup()
        self.test_translation_popup()
        self.test_error_popup()
        self.test_popup_state_management()
        self.test_clipboard_integration()
        self.test_callback_functionality()

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

        # ポップアップを閉じる
        if self.popup:
            self.popup.hide_popup()

    def run_interactive_test(self):
        """インタラクティブテスト（実際のUI表示）"""
        print("\n=== インタラクティブテスト ===")
        print("ポップアップが表示されます。手動でテストしてください。")
        print("テスト完了後、ウィンドウを閉じてください。")

        try:
            if not self.popup:
                print("ポップアップが作成されていません")
                return

            # テスト用のルートウィンドウ
            self.root = tk.Tk()
            self.root.withdraw()  # メインウィンドウを非表示

            # ステータスポップアップのテスト
            self.popup.show_status_popup("翻訳中...")

            # 3秒後に翻訳結果ポップアップを表示
            def show_result():
                result = TranslationResult(
                    source_text="Interactive test",
                    translated_text="インタラクティブテスト",
                    source_language="en",
                    target_language="ja",
                    status=TranslationStatus.COMPLETED,
                    timestamp=time.time(),
                    processing_time=1.0
                )
                self.popup.show_translation_popup(result)

            self.root.after(3000, show_result)

            # 10秒後にウィンドウを閉じる
            self.root.after(10000, self.root.quit)

            self.root.mainloop()

        except Exception as e:
            print(f"インタラクティブテストエラー: {e}")
        finally:
            if self.popup:
                self.popup.hide_popup()


def main():
    """メイン関数"""
    try:
        app = PopupWindowTestApp()

        # 自動テストを実行
        app.run_all_tests()

        # インタラクティブテストの実行を確認
        print("\nインタラクティブテストを実行しますか？ (y/n): ", end="")
        response = input().strip().lower()

        if response == 'y':
            app = PopupWindowTestApp()
            app.test_popup_creation()
            app.run_interactive_test()

    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
