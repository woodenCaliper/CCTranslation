"""
クリップボード管理システムのテスト

ClipboardManagerの動作確認を行う
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.clipboard_manager import ClipboardManager, ClipboardContent


class ClipboardTestApp:
    """クリップボードテストアプリケーション"""

    def __init__(self):
        self.manager = ClipboardManager()
        self.test_results = []

    def test_basic_functionality(self):
        """基本的な機能テスト"""
        print("=== 基本機能テスト ===")

        try:
            # テスト用テキスト
            test_text = "これは翻訳テスト用のテキストです。This is a test text for translation."

            # 1. クリップボードにテキストを設定
            print("1. クリップボードにテキストを設定...")
            self.manager.set_content(test_text)

            # 2. 内容を取得して確認
            print("2. クリップボード内容を取得...")
            content = self.manager.get_current_content()

            # 結果確認
            success = content.text == test_text
            print(f"   設定したテキスト: {test_text}")
            print(f"   取得したテキスト: {content.text}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("基本設定・取得", success))

            # 3. 翻訳用テキスト取得テスト
            print("3. 翻訳用テキスト取得...")
            translation_text = self.manager.get_text_for_translation()
            success = translation_text == test_text
            print(f"   翻訳対象テキスト: {translation_text}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("翻訳用テキスト取得", success))

            # 4. テキスト内容チェック
            print("4. テキスト内容チェック...")
            has_text = self.manager.is_text_content()
            print(f"   テキストが含まれているか: {has_text}")
            print(f"   結果: {'OK' if has_text else 'NG'}")

            self.test_results.append(("テキスト内容チェック", has_text))

        except Exception as e:
            print(f"NG 基本機能テストでエラー: {e}")
            self.test_results.append(("基本機能テスト", False))

    def test_empty_clipboard(self):
        """空クリップボードのテスト"""
        print("\n=== 空クリップボードテスト ===")

        try:
            # 1. クリップボードをクリア
            print("1. クリップボードをクリア...")
            self.manager.clear_content()

            # 2. 空かどうかチェック
            print("2. 空かどうかチェック...")
            has_text = self.manager.is_text_content()
            print(f"   テキストが含まれているか: {has_text}")
            print(f"   結果: {'OK' if not has_text else 'NG'}")

            self.test_results.append(("空クリップボードチェック", not has_text))

            # 3. 翻訳用テキスト取得（空の場合）
            print("3. 空の場合の翻訳用テキスト取得...")
            translation_text = self.manager.get_text_for_translation()
            success = translation_text is None
            print(f"   翻訳対象テキスト: {translation_text}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("空の場合の翻訳用テキスト取得", success))

        except Exception as e:
            print(f"NG 空クリップボードテストでエラー: {e}")
            self.test_results.append(("空クリップボードテスト", False))

    def test_content_info(self):
        """内容情報取得テスト"""
        print("\n=== 内容情報取得テスト ===")

        try:
            # テスト用テキストを設定
            test_text = "情報取得テスト用のテキストです。"
            self.manager.set_content(test_text)

            # 内容情報を取得
            print("1. 内容情報を取得...")
            info = self.manager.get_content_info()

            print(f"   情報: {info}")

            # 結果確認
            success = (
                info["has_text"] == True and
                info["length"] == len(test_text) and
                info["preview"] == test_text
            )

            print(f"   結果: {'OK' if success else 'NG'}")
            self.test_results.append(("内容情報取得", success))

        except Exception as e:
            print(f"NG 内容情報取得テストでエラー: {e}")
            self.test_results.append(("内容情報取得テスト", False))

    def test_callback_functionality(self):
        """コールバック機能テスト"""
        print("\n=== コールバック機能テスト ===")

        try:
            callback_called = False
            received_content = None

            def test_callback(content: ClipboardContent):
                nonlocal callback_called, received_content
                callback_called = True
                received_content = content
                print(f"   コールバック呼び出し: {content.length}文字")

            # コールバックを設定
            self.manager.set_change_callback(test_callback)

            # テキストを設定してコールバックが呼ばれるかテスト
            test_text = "コールバックテスト用テキスト"
            self.manager.set_content(test_text)

            # 少し待ってから結果を確認
            import time
            time.sleep(0.1)

            success = callback_called and received_content is not None
            print(f"   コールバック呼び出し: {callback_called}")
            print(f"   受信した内容: {received_content.text if received_content else None}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("コールバック機能", success))

        except Exception as e:
            print(f"NG コールバック機能テストでエラー: {e}")
            self.test_results.append(("コールバック機能テスト", False))

    def test_japanese_text(self):
        """日本語テキストのテスト"""
        print("\n=== 日本語テキストテスト ===")

        try:
            # 日本語テキストを設定
            japanese_text = "こんにちは、これは日本語のテストテキストです。"
            self.manager.set_content(japanese_text)

            # 内容を取得
            content = self.manager.get_current_content()

            success = content.text == japanese_text
            print(f"   設定したテキスト: {japanese_text}")
            print(f"   取得したテキスト: {content.text}")
            print(f"   文字数: {content.length}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("日本語テキスト処理", success))

        except Exception as e:
            print(f"NG 日本語テキストテストでエラー: {e}")
            self.test_results.append(("日本語テキストテスト", False))

    def test_long_text(self):
        """長文テキストのテスト"""
        print("\n=== 長文テキストテスト ===")

        try:
            # 長いテキストを生成
            long_text = "これは長いテキストのテストです。" * 100
            self.manager.set_content(long_text)

            # 内容を取得
            content = self.manager.get_current_content()

            success = content.text == long_text
            print(f"   設定したテキスト長: {len(long_text)}文字")
            print(f"   取得したテキスト長: {content.length}文字")
            print(f"   プレビュー: {content.text[:50]}...")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("長文テキスト処理", success))

        except Exception as e:
            print(f"NG 長文テキストテストでエラー: {e}")
            self.test_results.append(("長文テキストテスト", False))

    def run_all_tests(self):
        """全テストを実行"""
        print("======================================================================")
        print("クリップボード管理システム テスト開始")
        print("======================================================================")

        # 各テストを実行
        self.test_basic_functionality()
        self.test_empty_clipboard()
        self.test_content_info()
        self.test_callback_functionality()
        self.test_japanese_text()
        self.test_long_text()

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


def main():
    """メイン関数"""
    try:
        app = ClipboardTestApp()
        app.run_all_tests()
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()