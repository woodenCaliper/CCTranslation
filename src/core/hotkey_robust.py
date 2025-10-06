"""
Robust HotkeyManager - 堅牢なホットキー監視システム
日本語キーボード特殊キー対応強化版
"""

import time
import threading
from typing import Optional, Callable, Set
import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.exceptions import HotkeyError, JapaneseKeyboardError
from core.double_copy_detector import DoubleCopyDetector

# Windows API キーコード定義（win32conの代替）
class VK:
    """Windows仮想キーコード"""
    VK_CONTROL = 0x11
    VK_C = 0x43
    VK_KANJI = 0x19      # 全角半角キー（最重要）
    VK_CONVERT = 0x1C    # 変換キー
    VK_NONCONVERT = 0x1D # 無変換キー
    VK_KANA = 0x15       # カタカナひらがなキー
    VK_DBE_SBCSCHAR = 0xF3  # 半角/全角文字
    VK_DBE_DBCSCHAR = 0xF4  # 全角/半角文字

# pyWinhookのインポート
try:
    import pyWinhook as pyhook
    PYWINHOOK_AVAILABLE = True
except ImportError:
    PYWINHOOK_AVAILABLE = False
    print("警告: pyWinhookが利用できません。ホットキー機能は無効になります。")

class RobustHotkeyManager:
    """堅牢なホットキー監視クラス（日本語キーボード対応強化版）"""

    def __init__(self, callback_func: Optional[Callable] = None):
        """
        ホットキー管理の初期化

        Args:
            callback_func: ダブルコピー検出時のコールバック関数
        """
        if not PYWINHOOK_AVAILABLE:
            raise HotkeyError("pyWinhookが利用できません")

        self.callback_func = callback_func
        self.double_copy_detector = DoubleCopyDetector(callback_func)

        # 監視状態
        self.is_monitoring = False
        self.hook = None
        self.monitor_thread = None
        self.stop_event = threading.Event()

        # 日本語キーボード特殊キー（除外対象）
        self.excluded_keys: Set[int] = {
            VK.VK_KANJI,      # 全角半角キー（最重要）
            VK.VK_CONVERT,    # 変換キー
            VK.VK_NONCONVERT, # 無変換キー
            VK.VK_KANA,       # カタカナひらがなキー
            VK.VK_DBE_SBCSCHAR,  # 半角/全角文字
            VK.VK_DBE_DBCSCHAR,  # 全角/半角文字
        }

        # エラーハンドリング用
        self.error_count = 0
        self.max_errors = 5
        self.last_error_time = 0

    def _keyboard_hook(self, event):
        """
        キーボードイベントのフック処理（強化版）

        Args:
            event: キーボードイベント

        Returns:
            bool: True（イベントを続行）、False（イベントをブロック）
        """
        try:
            # エラー回数チェック
            if self.error_count >= self.max_errors:
                current_time = time.time()
                if current_time - self.last_error_time > 10:  # 10秒後にリセット
                    self.error_count = 0
                    print("ホットキー監視エラーカウンタをリセットしました")
                return True

            # 日本語キーボード特殊キーの除外
            if event.KeyID in self.excluded_keys:
                # 特殊キーは無視（ログ出力なし）
                return True

            # Ctrlキーの状態確認
            ctrl_pressed = event.KeyID == VK.VK_CONTROL or (
                hasattr(event, 'Control') and event.Control
            )

            # Ctrl+Cの検出
            if ctrl_pressed and event.KeyID == VK.VK_C and event.Message == 0x0100:  # WM_KEYDOWN
                self.double_copy_detector.on_copy_detected()

            return True

        except Exception as e:
            self.error_count += 1
            self.last_error_time = time.time()
            print(f"ホットキー監視エラー #{self.error_count}: {e}")

            # エラーが多すぎる場合は監視停止
            if self.error_count >= self.max_errors:
                print("ホットキー監視エラーが多すぎます。監視を停止します。")
                self.stop_monitoring()

            return True

    def _start_hook(self):
        """フック開始の内部処理"""
        try:
            if self.hook:
                return

            # pyWinhookのフック作成
            self.hook = pyhook.HookManager()
            self.hook.KeyDown = self._keyboard_hook

            # フック開始
            self.hook.HookKeyboard()

            print("ホットキー監視開始（堅牢版）")

            # メッセージループ
            import pythoncom
            while not self.stop_event.is_set():
                try:
                    pythoncom.PumpWaitingMessages()
                    time.sleep(0.01)
                except Exception as e:
                    print(f"メッセージループエラー: {e}")
                    break

        except Exception as e:
            print(f"フック開始エラー: {e}")
            raise HotkeyError(f"ホットキー監視開始に失敗: {e}")

    def start_monitoring(self):
        """ホットキー監視開始"""
        if self.is_monitoring:
            return

        if not PYWINHOOK_AVAILABLE:
            raise HotkeyError("pyWinhookが利用できません")

        try:
            self.is_monitoring = True
            self.stop_event.clear()

            # 別スレッドでフック開始
            self.monitor_thread = threading.Thread(
                target=self._start_hook,
                daemon=True,
                name="HotkeyMonitor"
            )
            self.monitor_thread.start()

            # 少し待機してフックが正常に開始されたか確認
            time.sleep(0.1)

            if self.monitor_thread.is_alive():
                print("ホットキー監視開始成功")
            else:
                raise HotkeyError("ホットキー監視スレッドの開始に失敗")

        except Exception as e:
            self.is_monitoring = False
            raise HotkeyError(f"ホットキー監視開始に失敗: {e}")

    def stop_monitoring(self):
        """ホットキー監視停止"""
        if not self.is_monitoring:
            return

        try:
            self.stop_event.set()

            # フック停止
            if self.hook:
                self.hook.UnhookKeyboard()
                self.hook = None

            # スレッド終了待機
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2.0)

            self.is_monitoring = False
            print("ホットキー監視停止")

        except Exception as e:
            print(f"ホットキー監視停止エラー: {e}")

    def is_running(self) -> bool:
        """監視状態の確認"""
        return self.is_monitoring

    def get_status(self) -> dict:
        """監視状態の詳細取得"""
        return {
            "is_monitoring": self.is_monitoring,
            "error_count": self.error_count,
            "thread_alive": self.monitor_thread.is_alive() if self.monitor_thread else False,
            "hook_active": self.hook is not None
        }

    def __del__(self):
        """デストラクタ"""
        try:
            self.stop_monitoring()
        except:
            pass


# 後方互換性のため
HotkeyManager = RobustHotkeyManager
