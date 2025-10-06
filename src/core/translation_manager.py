"""
Translation Manager - 翻訳エンジン統合システム

Google翻訳APIを使用した翻訳処理とタイムアウト管理
"""

import time
import threading
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.exceptions import TranslationError, TranslationTimeoutError, NetworkError


class TranslationStatus(Enum):
    """翻訳状態を表す列挙型"""
    IDLE = "idle"           # 待機中
    TRANSLATING = "translating"  # 翻訳中
    COMPLETED = "completed"  # 完了
    TIMEOUT = "timeout"     # タイムアウト
    ERROR = "error"         # エラー


@dataclass
class TranslationResult:
    """翻訳結果を表すデータクラス"""
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    status: TranslationStatus
    timestamp: float
    processing_time: float
    error_message: Optional[str] = None


class TranslationManager:
    """翻訳エンジン管理クラス"""

    def __init__(self, timeout_seconds: float = 3.0):
        """
        翻訳管理の初期化

        Args:
            timeout_seconds: タイムアウト時間（秒）
        """
        self.timeout_seconds = timeout_seconds
        self.current_translation: Optional[TranslationResult] = None
        self.status_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None

        # 翻訳状態
        self.status = TranslationStatus.IDLE
        self.translation_thread: Optional[threading.Thread] = None
        self.stop_translation = threading.Event()

        # googletransの初期化
        try:
            from googletrans import Translator
            self.translator = Translator()
            self.google_trans_available = True
            print("Google翻訳エンジン初期化完了")
        except ImportError:
            self.google_trans_available = False
            print("警告: googletransが利用できません。翻訳機能は無効になります。")
        except Exception as e:
            self.google_trans_available = False
            print(f"警告: Google翻訳エンジンの初期化に失敗: {e}")

    def set_status_callback(self, callback: Callable[[TranslationStatus, Optional[TranslationResult]], None]) -> None:
        """
        翻訳状態変更時のコールバック関数を設定

        Args:
            callback: 状態変更時に呼び出されるコールバック関数
        """
        self.status_callback = callback
        print("翻訳状態変更コールバックを設定しました")

    def set_completion_callback(self, callback: Callable[[TranslationResult], None]) -> None:
        """
        翻訳完了時のコールバック関数を設定

        Args:
            callback: 翻訳完了時に呼び出されるコールバック関数
        """
        self.completion_callback = callback
        print("翻訳完了コールバックを設定しました")

    def _update_status(self, new_status: TranslationStatus, result: Optional[TranslationResult] = None) -> None:
        """
        翻訳状態を更新

        Args:
            new_status: 新しい状態
            result: 翻訳結果（オプション）
        """
        self.status = new_status
        if self.status_callback:
            try:
                self.status_callback(new_status, result)
            except Exception as e:
                print(f"状態コールバック実行エラー: {e}")

    def _translate_text_sync(self, text: str, target_language: str, source_language: str = 'auto') -> TranslationResult:
        """
        同期翻訳処理

        Args:
            text: 翻訳対象テキスト
            target_language: 翻訳先言語
            source_language: 翻訳元言語（'auto'で自動検出）

        Returns:
            TranslationResult: 翻訳結果

        Raises:
            TranslationError: 翻訳処理に失敗した場合
        """
        start_time = time.time()

        try:
            if not self.google_trans_available:
                raise TranslationError("Google翻訳エンジンが利用できません")

            # 翻訳実行
            result = self.translator.translate(
                text,
                dest=target_language,
                src=source_language
            )

            processing_time = time.time() - start_time

            # 翻訳結果を作成
            translation_result = TranslationResult(
                source_text=text,
                translated_text=result.text,
                source_language=result.src,
                target_language=target_language,
                status=TranslationStatus.COMPLETED,
                timestamp=time.time(),
                processing_time=processing_time
            )

            print(f"翻訳完了: {processing_time:.2f}秒")
            return translation_result

        except Exception as e:
            processing_time = time.time() - start_time
            error_result = TranslationResult(
                source_text=text,
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                status=TranslationStatus.ERROR,
                timestamp=time.time(),
                processing_time=processing_time,
                error_message=str(e)
            )

            print(f"翻訳エラー: {e}")
            return error_result

    def translate_async(self, text: str, target_language: str, source_language: str = 'auto') -> None:
        """
        非同期翻訳処理（タイムアウト対応）

        Args:
            text: 翻訳対象テキスト
            target_language: 翻訳先言語
            source_language: 翻訳元言語（'auto'で自動検出）
        """
        if self.status == TranslationStatus.TRANSLATING:
            print("既に翻訳処理中です")
            return

        # 翻訳開始
        self.status = TranslationStatus.TRANSLATING
        self.stop_translation.clear()
        self.current_translation = None

        print(f"翻訳開始: {len(text)}文字 -> {target_language}")

        # 非同期翻訳スレッドを開始
        self.translation_thread = threading.Thread(
            target=self._translation_worker,
            args=(text, target_language, source_language),
            daemon=True
        )
        self.translation_thread.start()

        # 状態更新
        self._update_status(TranslationStatus.TRANSLATING)

    def _translation_worker(self, text: str, target_language: str, source_language: str) -> None:
        """
        翻訳ワーカースレッド

        Args:
            text: 翻訳対象テキスト
            target_language: 翻訳先言語
            source_language: 翻訳元言語
        """
        try:
            # 翻訳実行
            result = self._translate_text_sync(text, target_language, source_language)

            # 停止フラグをチェック
            if self.stop_translation.is_set():
                print("翻訳処理がキャンセルされました")
                return

            # 結果を保存
            self.current_translation = result

            # 状態更新
            if result.status == TranslationStatus.COMPLETED:
                self._update_status(TranslationStatus.COMPLETED, result)
                if self.completion_callback:
                    try:
                        self.completion_callback(result)
                    except Exception as e:
                        print(f"完了コールバック実行エラー: {e}")
            else:
                self._update_status(TranslationStatus.ERROR, result)

        except Exception as e:
            print(f"翻訳ワーカーエラー: {e}")
            error_result = TranslationResult(
                source_text=text,
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                status=TranslationStatus.ERROR,
                timestamp=time.time(),
                processing_time=0.0,
                error_message=str(e)
            )
            self.current_translation = error_result
            self._update_status(TranslationStatus.ERROR, error_result)

    def wait_for_completion(self, timeout: Optional[float] = None) -> Optional[TranslationResult]:
        """
        翻訳完了を待機

        Args:
            timeout: タイムアウト時間（Noneの場合は初期設定値を使用）

        Returns:
            Optional[TranslationResult]: 翻訳結果（タイムアウト時はNone）
        """
        if timeout is None:
            timeout = self.timeout_seconds

        if self.translation_thread and self.translation_thread.is_alive():
            self.translation_thread.join(timeout=timeout)

            # タイムアウトチェック
            if self.translation_thread.is_alive():
                print(f"翻訳処理がタイムアウトしました（{timeout}秒）")
                self.stop_translation.set()
                self._update_status(TranslationStatus.TIMEOUT)
                return None

        return self.current_translation

    def cancel_translation(self) -> None:
        """翻訳処理をキャンセル"""
        if self.status == TranslationStatus.TRANSLATING:
            print("翻訳処理をキャンセル中...")
            self.stop_translation.set()

            # スレッド終了を待つ
            if self.translation_thread and self.translation_thread.is_alive():
                self.translation_thread.join(timeout=1.0)

            self._update_status(TranslationStatus.IDLE)

    def get_status(self) -> Dict[str, Any]:
        """
        現在の翻訳状態を取得

        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            "status": self.status.value,
            "is_translating": self.status == TranslationStatus.TRANSLATING,
            "has_result": self.current_translation is not None,
            "thread_alive": self.translation_thread.is_alive() if self.translation_thread else False,
            "current_translation": self.current_translation
        }

    def translate_sync(self, text: str, target_language: str, source_language: str = 'auto') -> TranslationResult:
        """
        同期翻訳処理（テスト用）

        Args:
            text: 翻訳対象テキスト
            target_language: 翻訳先言語
            source_language: 翻訳元言語

        Returns:
            TranslationResult: 翻訳結果
        """
        return self._translate_text_sync(text, target_language, source_language)

    def reset(self) -> None:
        """翻訳状態をリセット"""
        self.cancel_translation()
        self.current_translation = None
        self.status = TranslationStatus.IDLE
        print("翻訳状態をリセットしました")


if __name__ == "__main__":
    # テストコード
    def status_callback(status: TranslationStatus, result: Optional[TranslationResult]):
        print(f"状態変更: {status.value}")
        if result:
            print(f"  結果: {result.status.value}")

    def completion_callback(result: TranslationResult):
        print(f"翻訳完了コールバック: {result.translated_text[:50]}...")

    print("=== TranslationManager テスト ===")

    manager = TranslationManager(timeout_seconds=3.0)
    manager.set_status_callback(status_callback)
    manager.set_completion_callback(completion_callback)

    # 同期翻訳テスト
    print("\n1. 同期翻訳テスト:")
    try:
        result = manager.translate_sync("Hello, world!", "ja", "en")
        print(f"   原文: {result.source_text}")
        print(f"   翻訳: {result.translated_text}")
        print(f"   処理時間: {result.processing_time:.2f}秒")
        print(f"   状態: {result.status.value}")
    except Exception as e:
        print(f"   エラー: {e}")

    # 非同期翻訳テスト
    print("\n2. 非同期翻訳テスト:")
    try:
        manager.translate_async("This is a test.", "ja", "en")

        # 結果を待機
        result = manager.wait_for_completion(timeout=5.0)
        if result:
            print(f"   原文: {result.source_text}")
            print(f"   翻訳: {result.translated_text}")
            print(f"   処理時間: {result.processing_time:.2f}秒")
        else:
            print("   タイムアウトまたはエラー")

    except Exception as e:
        print(f"   エラー: {e}")

    print("\n=== テスト完了 ===")
