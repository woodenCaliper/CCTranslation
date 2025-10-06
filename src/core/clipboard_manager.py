"""
Clipboard Manager - クリップボード管理システム

クリップボードからのテキスト取得と管理を行う
"""

import pyperclip
import time
from typing import Optional, Callable
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.exceptions import ClipboardError


@dataclass
class ClipboardContent:
    """クリップボード内容を表すデータクラス"""
    text: str
    timestamp: float
    length: int
    is_empty: bool


class ClipboardManager:
    """クリップボード管理クラス"""

    def __init__(self):
        """クリップボード管理の初期化"""
        self.last_content: Optional[ClipboardContent] = None
        self.change_callback: Optional[Callable] = None

        # クリップボード監視設定
        self.monitor_enabled = False
        self.monitor_thread = None
        self.stop_monitoring = False

        print("ClipboardManager初期化完了")

    def get_current_content(self) -> ClipboardContent:
        """
        現在のクリップボード内容を取得

        Returns:
            ClipboardContent: クリップボード内容

        Raises:
            ClipboardError: クリップボード取得に失敗した場合
        """
        try:
            # クリップボードからテキストを取得
            clipboard_text = pyperclip.paste()

            # 空チェック
            is_empty = not clipboard_text or clipboard_text.strip() == ""

            # 内容オブジェクトを作成
            content = ClipboardContent(
                text=clipboard_text if not is_empty else "",
                timestamp=time.time(),
                length=len(clipboard_text) if clipboard_text else 0,
                is_empty=is_empty
            )

            # 前回の内容と比較して変更があった場合のみコールバック実行
            if self.last_content is None or self.last_content.text != content.text:
                self.last_content = content
                if self.change_callback and not is_empty:
                    self.change_callback(content)

            return content

        except Exception as e:
            raise ClipboardError(f"クリップボード内容の取得に失敗しました: {e}")

    def set_content(self, text: str) -> None:
        """
        クリップボードにテキストを設定

        Args:
            text: 設定するテキスト

        Raises:
            ClipboardError: クリップボード設定に失敗した場合
        """
        try:
            pyperclip.copy(text)
            print(f"クリップボードにテキストを設定しました (長さ: {len(text)})")
        except Exception as e:
            raise ClipboardError(f"クリップボードへの設定に失敗しました: {e}")

    def clear_content(self) -> None:
        """クリップボード内容をクリア"""
        try:
            pyperclip.copy("")
            print("クリップボードをクリアしました")
        except Exception as e:
            raise ClipboardError(f"クリップボードのクリアに失敗しました: {e}")

    def set_change_callback(self, callback: Callable[[ClipboardContent], None]) -> None:
        """
        クリップボード変更時のコールバック関数を設定

        Args:
            callback: 変更時に呼び出されるコールバック関数
        """
        self.change_callback = callback
        print("クリップボード変更コールバックを設定しました")

    def get_text_for_translation(self) -> Optional[str]:
        """
        翻訳用のテキストを取得

        Returns:
            Optional[str]: 翻訳対象のテキスト（空の場合はNone）
        """
        try:
            content = self.get_current_content()

            if content.is_empty:
                print("クリップボードが空です")
                return None

            # テキストの前後空白をトリム
            text = content.text.strip()

            if not text:
                print("クリップボードに有効なテキストがありません")
                return None

            print(f"翻訳対象テキストを取得しました (長さ: {len(text)})")
            return text

        except ClipboardError as e:
            print(f"翻訳用テキストの取得に失敗: {e}")
            return None

    def is_text_content(self) -> bool:
        """
        クリップボードにテキストが含まれているかチェック

        Returns:
            bool: テキストが含まれている場合はTrue
        """
        try:
            content = self.get_current_content()
            return not content.is_empty and content.text.strip()
        except ClipboardError:
            return False

    def get_content_info(self) -> dict:
        """
        クリップボード内容の情報を取得

        Returns:
            dict: クリップボード内容の情報
        """
        try:
            content = self.get_current_content()
            return {
                "has_text": not content.is_empty,
                "length": content.length,
                "timestamp": content.timestamp,
                "preview": content.text[:50] + "..." if len(content.text) > 50 else content.text
            }
        except ClipboardError as e:
            return {
                "has_text": False,
                "length": 0,
                "timestamp": 0,
                "error": str(e)
            }


if __name__ == "__main__":
    # テストコード
    def clipboard_change_callback(content: ClipboardContent):
        print(f"クリップボード変更検出: {content.length}文字")
        print(f"内容プレビュー: {content.text[:30]}...")

    print("=== ClipboardManager テスト ===")

    manager = ClipboardManager()
    manager.set_change_callback(clipboard_change_callback)

    # 現在のクリップボード内容を確認
    print("\n1. 現在のクリップボード内容:")
    info = manager.get_content_info()
    print(f"   情報: {info}")

    # テスト用テキストをクリップボードに設定
    print("\n2. テスト用テキストをクリップボードに設定:")
    test_text = "Hello, this is a test text for translation."
    manager.set_content(test_text)

    # 設定後の内容を確認
    print("\n3. 設定後のクリップボード内容:")
    content = manager.get_current_content()
    print(f"   テキスト: {content.text}")
    print(f"   長さ: {content.length}")
    print(f"   空かどうか: {content.is_empty}")

    # 翻訳用テキスト取得テスト
    print("\n4. 翻訳用テキスト取得:")
    translation_text = manager.get_text_for_translation()
    print(f"   翻訳対象: {translation_text}")

    # テキスト内容チェック
    print("\n5. テキスト内容チェック:")
    has_text = manager.is_text_content()
    print(f"   テキストが含まれているか: {has_text}")

    print("\n=== テスト完了 ===")
    print("クリップボードに何かテキストをコピーしてから、このスクリプトを再実行してください。")
