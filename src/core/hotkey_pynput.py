"""
pynput使用版 HotkeyManager
日本語キーボード特殊キー対応版
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

# pynputのインポート
try:
    from pynput import keyboard
    from pynput.keyboard import Key, Listener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("警告: pynputが利用できません。ホットキー機能は無効になります。")

class PynputHotkeyManager:
    """pynput使用版ホットキー監視クラス"""

    def __init__(self, callback_func: Optional[Callable] = None):
        """
        ホットキー管理の初期化

        Args:
            callback_func: ダブルコピー検出時のコールバック関数
        """
        if not PYNPUT_AVAILABLE:
            raise HotkeyError("pynputが利用できません")

        self.callback_func = callback_func
        self.double_copy_detector = DoubleCopyDetector()
        if callback_func:
            self.double_copy_detector.set_callback(callback_func)

        # 監視状態
        self.is_monitoring = False
        self.listener = None
        self.monitor_thread = None
        self.stop_event = threading.Event()

        # 日本語キーボード特殊キー（除外対象）
        # pynputでは特殊キーは異なる名前で表現される
        self.excluded_keys: Set[Key] = {
            # 日本語キーボードの特殊キーはpynputでは直接サポートされていない
            # 代わりに、キーコードで判定する
        }

        # 除外するキーコード（Windows仮想キーコード）
        self.excluded_key_codes = {
            0x19,  # VK_KANJI (全角半角キー)
            0x1C,  # VK_CONVERT (変換キー)
            0x1D,  # VK_NONCONVERT (無変換キー)
            0x15,  # VK_KANA (カタカナひらがなキー)
            0xF3,  # VK_DBE_SBCSCHAR (半角/全角文字)
            0xF4,  # VK_DBE_DBCSCHAR (全角/半角文字)
        }

        # エラーハンドリング用
        self.error_count = 0
        self.max_errors = 5
        self.last_error_time = 0

    def _on_key_press(self, key):
        """
        キー押下時のイベント処理

        Args:
            key: 押下されたキー
        """
        try:
            # エラー回数チェック
            if self.error_count >= self.max_errors:
                current_time = time.time()
                if current_time - self.last_error_time > 10:  # 10秒後にリセット
                    self.error_count = 0
                    print("ホットキー監視エラーカウンタをリセットしました")
                return

            # デバッグ用：押されたキーを表示
            print(f"キー押下: {key}")

            # 日本語キーボード特殊キーの除外
            if hasattr(key, 'vk') and key.vk in self.excluded_key_codes:
                # 特殊キーは無視（ログ出力なし）
                print(f"特殊キー除外: {key}")
                return

            # Cキーの検出（大文字小文字両方）
            if (hasattr(key, 'char') and key.char and key.char.lower() == 'c') or \
               (hasattr(key, 'vk') and key.vk == 67):  # 'C'の仮想キーコード

                print(f"Cキー検出: {key}")

                # Ctrlキーが同時に押されているかチェック
                try:
                    controller = keyboard.Controller()
                    # より確実なCtrlキーチェック
                    ctrl_pressed = (controller.pressed(Key.ctrl_l) or
                                   controller.pressed(Key.ctrl_r) or
                                   hasattr(key, 'modifiers') and Key.ctrl in key.modifiers)

                    print(f"Ctrlキー状態: {ctrl_pressed}")

                    if ctrl_pressed:
                        print("Ctrl+C検出！")
                        self.double_copy_detector.detect_copy()

                except Exception as e:
                    print(f"Ctrlキーチェックエラー: {e}")

        except Exception as e:
            self.error_count += 1
            self.last_error_time = time.time()
            print(f"ホットキー監視エラー #{self.error_count}: {e}")

            # エラーが多すぎる場合は監視停止
            if self.error_count >= self.max_errors:
                print("ホットキー監視エラーが多すぎます。監視を停止します。")
                self.stop_monitoring()

    def _on_key_release(self, key):
        """
        キー解放時のイベント処理

        Args:
            key: 解放されたキー
        """
        # キー解放時は特に処理しない
        pass

    def _start_listener(self):
        """リスナー開始の内部処理"""
        try:
            # キーボードリスナーの作成
            self.listener = Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )

            # リスナー開始
            self.listener.start()

            print("ホットキー監視開始（pynput版）")

            # リスナーが停止するまで待機
            while not self.stop_event.is_set() and self.listener.running:
                time.sleep(0.1)

        except Exception as e:
            print(f"リスナー開始エラー: {e}")
            raise HotkeyError(f"ホットキー監視開始に失敗: {e}")

    def start_monitoring(self):
        """ホットキー監視開始"""
        if self.is_monitoring:
            return

        if not PYNPUT_AVAILABLE:
            raise HotkeyError("pynputが利用できません")

        try:
            self.is_monitoring = True
            self.stop_event.clear()

            # 別スレッドでリスナー開始
            self.monitor_thread = threading.Thread(
                target=self._start_listener,
                daemon=True,
                name="PynputHotkeyMonitor"
            )
            self.monitor_thread.start()

            # 少し待機してリスナーが正常に開始されたか確認
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

            # リスナー停止
            if self.listener:
                self.listener.stop()
                self.listener = None

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
            "listener_running": self.listener.running if self.listener else False
        }

    def __del__(self):
        """デストラクタ"""
        try:
            self.stop_monitoring()
        except:
            pass


# 後方互換性のため
HotkeyManager = PynputHotkeyManager
