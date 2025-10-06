"""
翻訳エンジン統合システムのテスト

TranslationManagerの動作確認を行う
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import time
from typing import Optional
from core.translation_manager import TranslationManager, TranslationStatus, TranslationResult


class TranslationTestApp:
    """翻訳テストアプリケーション"""

    def __init__(self):
        self.manager = TranslationManager(timeout_seconds=3.0)
        self.test_results = []
        self.status_changes = []
        self.completion_calls = []

    def setup_callbacks(self):
        """コールバック関数を設定"""
        def status_callback(status: TranslationStatus, result: Optional[TranslationResult]):
            self.status_changes.append((status, result))
            print(f"   状態変更: {status.value}")

        def completion_callback(result: TranslationResult):
            self.completion_calls.append(result)
            print(f"   完了コールバック: {result.translated_text[:30]}...")

        self.manager.set_status_callback(status_callback)
        self.manager.set_completion_callback(completion_callback)

    def test_basic_translation(self):
        """基本翻訳テスト"""
        print("=== 基本翻訳テスト ===")

        try:
            # テスト用テキスト
            test_text = "Hello, world!"
            target_language = "ja"

            print(f"1. 翻訳実行: '{test_text}' -> {target_language}")

            # 同期翻訳テスト
            result = self.manager.translate_sync(test_text, target_language, "en")

            # 結果確認
            success = (
                result.status == TranslationStatus.COMPLETED and
                result.source_text == test_text and
                len(result.translated_text) > 0 and
                result.target_language == target_language
            )

            print(f"   原文: {result.source_text}")
            print(f"   翻訳: {result.translated_text}")
            print(f"   処理時間: {result.processing_time:.2f}秒")
            print(f"   状態: {result.status.value}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("基本翻訳", success))

        except Exception as e:
            print(f"NG 基本翻訳テストでエラー: {e}")
            self.test_results.append(("基本翻訳テスト", False))

    def test_async_translation(self):
        """非同期翻訳テスト"""
        print("\n=== 非同期翻訳テスト ===")

        try:
            # コールバックを設定
            self.setup_callbacks()
            self.status_changes.clear()
            self.completion_calls.clear()

            # テスト用テキスト
            test_text = "This is an async translation test."
            target_language = "ja"

            print(f"1. 非同期翻訳開始: '{test_text}' -> {target_language}")

            # 非同期翻訳実行
            self.manager.translate_async(test_text, target_language, "en")

            # 結果を待機
            result = self.manager.wait_for_completion(timeout=5.0)

            # 結果確認
            success = (
                result is not None and
                result.status == TranslationStatus.COMPLETED and
                result.source_text == test_text and
                len(result.translated_text) > 0
            )

            print(f"   原文: {result.source_text if result else 'None'}")
            print(f"   翻訳: {result.translated_text if result else 'None'}")
            print(f"   処理時間: {result.processing_time:.2f}秒" if result else "N/A")
            print(f"   状態変更回数: {len(self.status_changes)}")
            print(f"   完了コールバック回数: {len(self.completion_calls)}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("非同期翻訳", success))

        except Exception as e:
            print(f"NG 非同期翻訳テストでエラー: {e}")
            self.test_results.append(("非同期翻訳テスト", False))

    def test_timeout_handling(self):
        """タイムアウト処理テスト"""
        print("\n=== タイムアウト処理テスト ===")

        try:
            # コールバックを設定
            self.setup_callbacks()
            self.status_changes.clear()

            # 短いタイムアウトでテスト
            self.manager.timeout_seconds = 1.0

            test_text = "This is a timeout test."
            target_language = "ja"

            print(f"1. タイムアウトテスト開始: タイムアウト1秒")

            # 非同期翻訳実行
            self.manager.translate_async(test_text, target_language, "en")

            # 短い時間で結果を待機（タイムアウトをテスト）
            result = self.manager.wait_for_completion(timeout=0.5)

            # タイムアウト状態をチェック
            status_info = self.manager.get_status()
            timeout_occurred = status_info["status"] == "timeout"

            print(f"   待機結果: {'タイムアウト' if result is None else '完了'}")
            print(f"   状態: {status_info['status']}")
            print(f"   結果: {'OK' if timeout_occurred else 'NG'}")

            self.test_results.append(("タイムアウト処理", timeout_occurred))

        except Exception as e:
            print(f"NG タイムアウト処理テストでエラー: {e}")
            self.test_results.append(("タイムアウト処理テスト", False))

    def test_japanese_translation(self):
        """日本語翻訳テスト"""
        print("\n=== 日本語翻訳テスト ===")

        try:
            # 日本語テキストを英語に翻訳
            japanese_text = "こんにちは、世界！"
            target_language = "en"

            print(f"1. 日本語翻訳: '{japanese_text}' -> {target_language}")

            result = self.manager.translate_sync(japanese_text, target_language, "ja")

            success = (
                result.status == TranslationStatus.COMPLETED and
                result.source_text == japanese_text and
                len(result.translated_text) > 0 and
                result.source_language == "ja"
            )

            print(f"   原文: {result.source_text}")
            print(f"   翻訳: {result.translated_text}")
            print(f"   処理時間: {result.processing_time:.2f}秒")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("日本語翻訳", success))

        except Exception as e:
            print(f"NG 日本語翻訳テストでエラー: {e}")
            self.test_results.append(("日本語翻訳テスト", False))

    def test_auto_language_detection(self):
        """自動言語検出テスト"""
        print("\n=== 自動言語検出テスト ===")

        try:
            # 英語テキスト（自動検出）
            english_text = "This is an auto-detection test."
            target_language = "ja"

            print(f"1. 自動検出テスト: '{english_text}' -> {target_language}")

            result = self.manager.translate_sync(english_text, target_language, "auto")

            success = (
                result.status == TranslationStatus.COMPLETED and
                result.source_language == "en" and  # 自動検出された言語
                len(result.translated_text) > 0
            )

            print(f"   原文: {result.source_text}")
            print(f"   翻訳: {result.translated_text}")
            print(f"   検出された言語: {result.source_language}")
            print(f"   処理時間: {result.processing_time:.2f}秒")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("自動言語検出", success))

        except Exception as e:
            print(f"NG 自動言語検出テストでエラー: {e}")
            self.test_results.append(("自動言語検出テスト", False))

    def test_long_text_translation(self):
        """長文翻訳テスト"""
        print("\n=== 長文翻訳テスト ===")

        try:
            # 長いテキスト
            long_text = "This is a long text translation test. " * 10
            target_language = "ja"

            print(f"1. 長文翻訳: {len(long_text)}文字 -> {target_language}")

            result = self.manager.translate_sync(long_text, target_language, "en")

            success = (
                result.status == TranslationStatus.COMPLETED and
                result.source_text == long_text and
                len(result.translated_text) > 0
            )

            print(f"   原文長: {len(result.source_text)}文字")
            print(f"   翻訳長: {len(result.translated_text)}文字")
            print(f"   処理時間: {result.processing_time:.2f}秒")
            print(f"   プレビュー: {result.translated_text[:50]}...")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("長文翻訳", success))

        except Exception as e:
            print(f"NG 長文翻訳テストでエラー: {e}")
            self.test_results.append(("長文翻訳テスト", False))

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n=== エラーハンドリングテスト ===")

        try:
            # 無効な言語コードでテスト
            test_text = "This is an error test."
            invalid_language = "invalid_lang_code"

            print(f"1. エラーテスト: 無効な言語コード '{invalid_language}'")

            result = self.manager.translate_sync(test_text, invalid_language, "en")

            # エラー状態をチェック
            success = result.status == TranslationStatus.ERROR

            print(f"   状態: {result.status.value}")
            print(f"   エラーメッセージ: {result.error_message}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("エラーハンドリング", success))

        except Exception as e:
            print(f"NG エラーハンドリングテストでエラー: {e}")
            self.test_results.append(("エラーハンドリングテスト", False))

    def test_status_management(self):
        """状態管理テスト"""
        print("\n=== 状態管理テスト ===")

        try:
            # 初期状態チェック
            initial_status = self.manager.get_status()

            # 翻訳開始
            self.manager.translate_async("Status test", "ja", "en")
            translating_status = self.manager.get_status()

            # 結果待機
            result = self.manager.wait_for_completion(timeout=5.0)
            final_status = self.manager.get_status()

            success = (
                initial_status["status"] == "idle" and
                translating_status["is_translating"] == True and
                final_status["has_result"] == True
            )

            print(f"   初期状態: {initial_status['status']}")
            print(f"   翻訳中状態: {translating_status['status']}")
            print(f"   最終状態: {final_status['status']}")
            print(f"   結果: {'OK' if success else 'NG'}")

            self.test_results.append(("状態管理", success))

        except Exception as e:
            print(f"NG 状態管理テストでエラー: {e}")
            self.test_results.append(("状態管理テスト", False))

    def run_all_tests(self):
        """全テストを実行"""
        print("======================================================================")
        print("翻訳エンジン統合システム テスト開始")
        print("======================================================================")

        # 各テストを実行
        self.test_basic_translation()
        self.test_async_translation()
        self.test_timeout_handling()
        self.test_japanese_translation()
        self.test_auto_language_detection()
        self.test_long_text_translation()
        self.test_error_handling()
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


def main():
    """メイン関数"""
    try:
        app = TranslationTestApp()
        app.run_all_tests()
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
