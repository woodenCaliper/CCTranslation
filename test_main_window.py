"""
メインウィンドウUIのテスト

MainWindowの動作確認を行う
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from tkinter import messagebox
import threading
import time

from ui.main_window import MainWindow
from data.config import ConfigManager
from data.language import LanguageManager


class MainWindowTestApp:
    """メインウィンドウテストアプリケーション"""

    def __init__(self):
        self.test_results = []
        self.window = None

    def test_window_creation(self):
        """ウィンドウ作成テスト"""
        print("=== ウィンドウ作成テスト ===")

        try:
            # 設定と言語管理の初期化
            config_manager = ConfigManager()
            language_manager = LanguageManager()

            # メインウィンドウの作成
            self.window = MainWindow(config_manager, language_manager)

            # ウィンドウの基本プロパティをチェック
            success = (
                self.window.root is not None and
                self.window.translation_manager is not None and
                self.window.clipboard_manager is not None and
                self.window.source_text is not None and
                self.window.target_text is not None
            )

            print(f"   ウィンドウ作成: {'OK' if success else 'NG'}")
            print(f"   翻訳マネージャー: {'OK' if self.window.translation_manager else 'NG'}")
            print(f"   クリップボードマネージャー: {'OK' if self.window.clipboard_manager else 'NG'}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("ウィンドウ作成", success))

        except Exception as e:
            print(f"NG ウィンドウ作成テストでエラー: {e}")
            self.test_results.append(("ウィンドウ作成テスト", False))

    def test_theme_switching(self):
        """テーマ切り替えテスト"""
        print("\n=== テーマ切り替えテスト ===")

        try:
            if not self.window:
                print("   ウィンドウが作成されていません")
                self.test_results.append(("テーマ切り替え", False))
                return

            # 初期テーマを確認
            initial_theme = self.window.current_theme
            print(f"   初期テーマ: {initial_theme}")

            # テーマ切り替え
            self.window.toggle_theme()
            new_theme = self.window.current_theme
            print(f"   切り替え後テーマ: {new_theme}")

            # 再度切り替え
            self.window.toggle_theme()
            final_theme = self.window.current_theme
            print(f"   最終テーマ: {final_theme}")

            success = (
                initial_theme != new_theme and
                final_theme == initial_theme
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("テーマ切り替え", success))

        except Exception as e:
            print(f"NG テーマ切り替えテストでエラー: {e}")
            self.test_results.append(("テーマ切り替えテスト", False))

    def test_language_selection(self):
        """言語選択テスト"""
        print("\n=== 言語選択テスト ===")

        try:
            if not self.window:
                print("   ウィンドウが作成されていません")
                self.test_results.append(("言語選択", False))
                return

            # 言語リストの更新
            self.window.update_language_lists()

            # 翻訳元言語の選択
            self.window.source_lang_var.set("自動検出 (auto)")
            source_code = self.window.get_selected_language_code(self.window.source_lang_var.get())

            # 翻訳先言語の選択
            self.window.target_lang_var.set("日本語 (ja)")
            target_code = self.window.get_selected_language_code(self.window.target_lang_var.get())

            print(f"   翻訳元言語: {source_code}")
            print(f"   翻訳先言語: {target_code}")

            success = (source_code == "auto" and target_code == "ja")

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("言語選択", success))

        except Exception as e:
            print(f"NG 言語選択テストでエラー: {e}")
            self.test_results.append(("言語選択テスト", False))

    def test_text_input(self):
        """テキスト入力テスト"""
        print("\n=== テキスト入力テスト ===")

        try:
            if not self.window:
                print("   ウィンドウが作成されていません")
                self.test_results.append(("テキスト入力", False))
                return

            # テストテキストの入力
            test_text = "Hello, this is a test text."
            self.window.source_text.delete("1.0", tk.END)
            self.window.source_text.insert("1.0", test_text)

            # 入力されたテキストを確認
            input_text = self.window.source_text.get("1.0", tk.END).strip()

            # 翻訳ボタンの状態を確認
            button_state = self.window.translate_button['state']

            print(f"   入力テキスト: {input_text}")
            print(f"   翻訳ボタン状態: {button_state}")

            success = (
                input_text == test_text and
                button_state == tk.NORMAL
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("テキスト入力", success))

        except Exception as e:
            print(f"NG テキスト入力テストでエラー: {e}")
            self.test_results.append(("テキスト入力テスト", False))

    def test_clipboard_operations(self):
        """クリップボード操作テスト"""
        print("\n=== クリップボード操作テスト ===")

        try:
            if not self.window:
                print("   ウィンドウが作成されていません")
                self.test_results.append(("クリップボード操作", False))
                return

            # テストテキストをクリップボードに設定
            test_text = "This is a clipboard test."
            self.window.clipboard_manager.set_content(test_text)

            # クリップボードから読み込み
            self.window.load_from_clipboard()

            # 読み込まれたテキストを確認
            loaded_text = self.window.source_text.get("1.0", tk.END).strip()

            print(f"   設定したテキスト: {test_text}")
            print(f"   読み込まれたテキスト: {loaded_text}")

            success = (loaded_text == test_text)

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("クリップボード操作", success))

        except Exception as e:
            print(f"NG クリップボード操作テストでエラー: {e}")
            self.test_results.append(("クリップボード操作テスト", False))

    def test_translation_workflow(self):
        """翻訳ワークフローテスト"""
        print("\n=== 翻訳ワークフローテスト ===")

        try:
            if not self.window:
                print("   ウィンドウが作成されていません")
                self.test_results.append(("翻訳ワークフロー", False))
                return

            # 翻訳元テキストを設定
            source_text = "Hello, world!"
            self.window.source_text.delete("1.0", tk.END)
            self.window.source_text.insert("1.0", source_text)

            # 言語設定
            self.window.source_lang_var.set("英語 (en)")
            self.window.target_lang_var.set("日本語 (ja)")

            print(f"   翻訳元テキスト: {source_text}")
            print(f"   翻訳元言語: {self.window.get_selected_language_code(self.window.source_lang_var.get())}")
            print(f"   翻訳先言語: {self.window.get_selected_language_code(self.window.target_lang_var.get())}")

            # 翻訳実行（同期版）
            source_lang = self.window.get_selected_language_code(self.window.source_lang_var.get())
            target_lang = self.window.get_selected_language_code(self.window.target_lang_var.get())

            result = self.window.translation_manager.translate_sync(source_text, target_lang, source_lang)

            if result and result.status.name == "COMPLETED":
                # 翻訳結果を表示エリアに設定
                self.window.target_text.config(state=tk.NORMAL)
                self.window.target_text.delete("1.0", tk.END)
                self.window.target_text.insert("1.0", result.translated_text)
                self.window.target_text.config(state=tk.DISABLED)

                print(f"   翻訳結果: {result.translated_text}")
                print(f"   処理時間: {result.processing_time:.2f}秒")

                success = True
            else:
                print(f"   翻訳失敗: {result.error_message if result else 'Unknown error'}")
                success = False

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("翻訳ワークフロー", success))

        except Exception as e:
            print(f"NG 翻訳ワークフローテストでエラー: {e}")
            self.test_results.append(("翻訳ワークフローテスト", False))

    def test_ui_responsiveness(self):
        """UI応答性テスト"""
        print("\n=== UI応答性テスト ===")

        try:
            if not self.window:
                print("   ウィンドウが作成されていません")
                self.test_results.append(("UI応答性", False))
                return

            # ウィンドウのサイズ変更テスト
            original_size = self.window.root.geometry()
            self.window.root.geometry("1000x700")

            # テキストエリアの状態確認
            source_text_exists = self.window.source_text is not None
            target_text_exists = self.window.target_text is not None

            # ボタンの状態確認
            translate_button_exists = self.window.translate_button is not None
            load_button_exists = self.window.load_button is not None
            copy_button_exists = self.window.copy_button is not None

            print(f"   ウィンドウサイズ変更: OK")
            print(f"   テキストエリア存在: 翻訳元={source_text_exists}, 翻訳先={target_text_exists}")
            print(f"   ボタン存在: 翻訳={translate_button_exists}, 読み込み={load_button_exists}, コピー={copy_button_exists}")

            success = (
                source_text_exists and
                target_text_exists and
                translate_button_exists and
                load_button_exists and
                copy_button_exists
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("UI応答性", success))

        except Exception as e:
            print(f"NG UI応答性テストでエラー: {e}")
            self.test_results.append(("UI応答性テスト", False))

    def run_all_tests(self):
        """全テストを実行"""
        print("======================================================================")
        print("メインウィンドウUI テスト開始")
        print("======================================================================")

        # 各テストを実行
        self.test_window_creation()
        self.test_theme_switching()
        self.test_language_selection()
        self.test_text_input()
        self.test_clipboard_operations()
        self.test_translation_workflow()
        self.test_ui_responsiveness()

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

        # ウィンドウを閉じる
        if self.window:
            self.window.root.destroy()

    def run_interactive_test(self):
        """インタラクティブテスト（実際のUI表示）"""
        print("\n=== インタラクティブテスト ===")
        print("UIが表示されます。手動でテストしてください。")
        print("テスト完了後、ウィンドウを閉じてください。")

        try:
            if self.window:
                self.window.run()
        except Exception as e:
            print(f"インタラクティブテストエラー: {e}")


def main():
    """メイン関数"""
    try:
        app = MainWindowTestApp()

        # 自動テストを実行
        app.run_all_tests()

        # インタラクティブテストの実行を確認
        print("\nインタラクティブテストを実行しますか？ (y/n): ", end="")
        response = input().strip().lower()

        if response == 'y':
            app = MainWindowTestApp()
            app.test_window_creation()
            app.run_interactive_test()

    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
