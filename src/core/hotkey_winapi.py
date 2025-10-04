"""
Windows API直接使用版 HotkeyManager
日本語キーボード特殊キー対応の最終版
"""

import time
import threading
from typing import Optional, Callable
import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.exceptions import HotkeyError, JapaneseKeyboardError
from core.double_copy_detector import DoubleCopyDetector

# Windows API キーコード定義
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

# Windows API インポート
try:
    import win32api
    import win32con
    import win32gui
    import ctypes
    from ctypes import wintypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("警告: Windows APIが利用できません。ホットキー機能は無効になります。")

# Windows API 定数
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
HC_ACTION = 0

class WinAPIHotkeyManager:
    """Windows API直接使用版ホットキー監視クラス"""

    def __init__(self, callback_func: Optional[Callable] = None):
        """
        ホットキー管理の初期化

        Args:
            callback_func: ダブルコピー検出時のコールバック関数
        """
        if not WIN32_AVAILABLE:
            raise HotkeyError("Windows APIが利用できません")

        self.callback_func = callback_func
        self.double_copy_detector = DoubleCopyDetector(callback_func)

        # 監視状態
        self.is_monitoring = False
        self.hook = None
        self.monitor_thread = None
        self.stop_event = threading.Event()

        # 日本語キーボード特殊キー（除外対象）
        self.excluded_keys = {
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

    def _low_level_keyboard_proc(self, nCode, wParam, lParam):
        """
        低レベルキーボードプロシージャ

        Args:
            nCode: フックコード
            wParam: メッセージ識別子
            lParam: キーボード情報へのポインタ

        Returns:
            int: 次のフックプロシージャへの呼び出し結果
        """
        try:
            # エラー回数チェック
            if self.error_count >= self.max_errors:
                current_time = time.time()
                if current_time - self.last_error_time > 10:  # 10秒後にリセット
                    self.error_count = 0
                    print("ホットキー監視エラーカウンタをリセットしました")
                return ctypes.windll.user32.CallNextHookExW(self.hook, nCode, wParam, lParam)

            if nCode >= HC_ACTION:
                # キーボード情報の取得
                kb_info = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

                # 日本語キーボード特殊キーの除外
                if kb_info.vkCode in self.excluded_keys:
                    # 特殊キーは無視（ログ出力なし）
                    return ctypes.windll.user32.CallNextHookExW(self.hook, nCode, wParam, lParam)

                # Ctrl+Cの検出（キー押下のみ）
                if wParam == WM_KEYDOWN:
                    ctrl_pressed = (win32api.GetAsyncKeyState(VK.VK_CONTROL) & 0x8000) != 0

                    if ctrl_pressed and kb_info.vkCode == VK.VK_C:
                        self.double_copy_detector.on_copy_detected()

            # 次のフックプロシージャに渡す
            return ctypes.windll.user32.CallNextHookExW(self.hook, nCode, wParam, lParam)

        except Exception as e:
            self.error_count += 1
            self.last_error_time = time.time()
            print(f"ホットキー監視エラー #{self.error_count}: {e}")

            # エラーが多すぎる場合は監視停止
            if self.error_count >= self.max_errors:
                print("ホットキー監視エラーが多すぎます。監視を停止します。")
                self.stop_monitoring()

            return ctypes.windll.user32.CallNextHookExW(self.hook, nCode, wParam, lParam)

    def _start_hook(self):
        """フック開始の内部処理"""
        try:
            # フックプロシージャの定義
            HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
            hook_proc = HOOKPROC(self._low_level_keyboard_proc)

            # 低レベルキーボードフックの設定
            self.hook = ctypes.windll.user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                hook_proc,
                ctypes.windll.kernel32.GetModuleHandleW(None),
                0
            )

            if not self.hook:
                raise HotkeyError("フックの設定に失敗しました")

            print("ホットキー監視開始（Windows API直接版）")

            # メッセージループ
            msg = wintypes.MSG()
            while not self.stop_event.is_set():
                try:
                    # メッセージの取得（非ブロッキング）
                    ret = ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)
                    if ret:
                        ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                        ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
                    else:
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

        if not WIN32_AVAILABLE:
            raise HotkeyError("Windows APIが利用できません")

        try:
            self.is_monitoring = True
            self.stop_event.clear()

            # 別スレッドでフック開始
            self.monitor_thread = threading.Thread(
                target=self._start_hook,
                daemon=True,
                name="WinAPIHotkeyMonitor"
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
                ctypes.windll.user32.UnhookWindowsHookEx(self.hook)
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


# KBDLLHOOKSTRUCT構造体の定義
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('vkCode', wintypes.DWORD),
        ('scanCode', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
    ]


# 後方互換性のため
HotkeyManager = WinAPIHotkeyManager
