"""Windows グローバルホットキー用のアダプター。

実運用では :mod:`pyWinhook` と :mod:`pythoncom` を利用して
`Ctrl + C` の押下イベントを監視する。テスト環境やモジュールが
利用できない環境ではスタブとして動作し、アプリケーション側で
機能を無効化できるようになっている。
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional


LOGGER = logging.getLogger(__name__)


class KeyboardAdapter:
    """グローバルコピーイベントを監視するアダプター。"""

    def __init__(self, on_copy: Callable[[], None]) -> None:
        self._on_copy = on_copy
        self._hook_manager = None
        self._pythoncom = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._available = False
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        try:
            import pythoncom
            import pyWinhook
        except ImportError:
            LOGGER.warning(
                "pyWinhook もしくは pythoncom が見つかりません。"
                "キーボードフック機能は無効化されます。"
            )
            self._available = False
            return

        self._pythoncom = pythoncom
        self._hook_manager = pyWinhook.HookManager()
        self._hook_manager.KeyDown = self._on_key_down
        self._available = True

    # Windows 仮想キーコード
    _VK_C = 0x43
    _VK_CONTROL = 0x11

    def _on_key_down(self, event) -> bool:  # pragma: no cover - Windows 専用経路
        ctrl_pressed = event.KeyID == self._VK_C and event.Alt == 0 and event.Shift == 0
        if ctrl_pressed and event.KeyID == self._VK_C and event.IsCtrl():
            try:
                self._on_copy()
            except Exception:  # 安全策
                LOGGER.exception("on_copy コールバックの実行に失敗しました")
        return True

    def start(self) -> None:
        """キーボードフックを開始する。"""

        if not self._available:
            raise RuntimeError("キーボードフック機能は利用できません。")
        if self._running.is_set():
            return

        def _loop():  # pragma: no cover - Windows 専用経路
            assert self._hook_manager is not None
            assert self._pythoncom is not None
            self._hook_manager.HookKeyboard()
            self._running.set()
            try:
                while self._running.is_set():
                    self._pythoncom.PumpWaitingMessages()
            finally:
                self._hook_manager.UnhookKeyboard()

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._running.is_set():
            return
        self._running.clear()
        if self._thread and self._thread.is_alive():  # pragma: no cover - Windows 専用経路
            self._thread.join(timeout=1.0)

    def is_available(self) -> bool:
        """利用可能かどうかを返す。"""

        return self._available


__all__ = ["KeyboardAdapter"]

