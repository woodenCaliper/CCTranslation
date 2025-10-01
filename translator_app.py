"""CCTranslation メインアプリケーション。

Tkinter を利用したポップアップ UI と、クリップボードのダブル
コピー検出による翻訳トリガーを提供する。Windows 常駐ユーティ
リティとして動作することを想定しつつ、Linux/macOS 上でも単発
翻訳モードやユニットテストが実行できるよう、依存コンポーネン
トを差し替えられる構造を採用している。
"""

from __future__ import annotations

import argparse
import logging
import queue
import socket
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

try:  # pragma: no cover - 環境依存
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:  # pragma: no cover - 環境依存
    tk = None
    ttk = None
    messagebox = None

try:  # pragma: no cover - 任意機能
    import pyperclip
except Exception:  # pragma: no cover - 任意機能
    pyperclip = None

try:  # pragma: no cover - 任意機能
    import pystray
    from PIL import Image
except Exception:  # pragma: no cover - 任意機能
    pystray = None
    Image = None

from translation_service import TranslationResult, TranslationService

LOGGER = logging.getLogger(__name__)


def resource_path(relative: str) -> str:
    """PyInstaller 対応のリソースパス解決関数。"""

    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return str(Path(base_path, relative))


class DoubleCopyDetector:
    """ダブルコピー (Ctrl + C 連続押下) を検出するユーティリティ。"""

    def __init__(self, interval: float = 0.5) -> None:
        self.interval = interval
        self._last_trigger = 0.0
        self._lock = threading.Lock()

    def register_copy(self, timestamp: Optional[float] = None) -> bool:
        now = timestamp if timestamp is not None else time.monotonic()
        with self._lock:
            if now - self._last_trigger <= self.interval:
                self._last_trigger = 0.0
                return True
            self._last_trigger = now
            return False


class ClipboardInterface:
    """クリップボードからテキストを取得するインターフェース。"""

    def get_text(self) -> str:
        raise NotImplementedError


class PyperclipClipboard(ClipboardInterface):  # pragma: no cover - pyperclip 依存
    def __init__(self) -> None:
        if pyperclip is None:
            raise RuntimeError("pyperclip がインストールされていません。")

    def get_text(self) -> str:
        assert pyperclip is not None
        return pyperclip.paste() or ""


class DummyClipboard(ClipboardInterface):
    """テスト用のメモリ内クリップボード。"""

    def __init__(self) -> None:
        self.text = ""

    def set_text(self, text: str) -> None:
        self.text = text

    def get_text(self) -> str:
        return self.text


@dataclass
class TranslationPayload:
    request_text: str
    result: TranslationResult


class TranslationWorker(threading.Thread):
    """バックグラウンドで翻訳を実行するスレッド。"""

    def __init__(
        self,
        request_text: str,
        queue_: "queue.Queue[TranslationPayload]",
        translation_service: TranslationService,
        dest_language: str,
        source_language: str,
    ) -> None:
        super().__init__(daemon=True)
        self._text = request_text
        self._queue = queue_
        self._service = translation_service
        self._dest = dest_language
        self._src = source_language

    def run(self) -> None:
        try:
            result = self._service.translate(
                self._text,
                dest_language=self._dest,
                source_language=self._src,
            )
            payload = TranslationPayload(request_text=self._text, result=result)
            self._queue.put(payload)
        except Exception as exc:  # pragma: no cover - 例外経路
            LOGGER.exception("翻訳処理に失敗しました")
            self._queue.put(exc)


class SystemTrayController:  # pragma: no cover - 任意機能
    """pystray を利用したシステムトレイ制御。"""

    def __init__(self, on_show: Callable[[], None], on_quit: Callable[[], None]) -> None:
        self._on_show = on_show
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        if pystray and Image:
            image = Image.new("RGB", (64, 64), color=(30, 30, 30))
            menu = pystray.Menu(
                pystray.MenuItem("Show", lambda icon: self._on_show()),
                pystray.MenuItem("Quit", lambda icon: self._on_quit()),
            )
            self._icon = pystray.Icon("CCTranslation", image, "CCTranslation", menu)

    def run_detached(self) -> None:
        if self._icon:
            threading.Thread(target=self._icon.run, daemon=True).start()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()


class SingleInstanceGuard:
    """単一インスタンス実行を保証する簡易ガード。"""

    def __init__(self, name: str) -> None:
        self._name = name
        self._socket: Optional[socket.socket] = None

    def acquire(self) -> bool:
        port = 40000 + (hash(self._name) % 10000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
        sock.listen(1)
        self._socket = sock
        return True

    def release(self) -> None:
        if self._socket:
            self._socket.close()
            self._socket = None


class TranslatorApp:
    """アプリケーション本体。"""

    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 400

    def __init__(
        self,
        *,
        dest_language: str = "ja",
        source_language: str = "auto",
        double_copy_interval: float = 0.5,
        clipboard: Optional[ClipboardInterface] = None,
        translation_service: Optional[TranslationService] = None,
        enable_ui: bool = True,
    ) -> None:
        self.dest_language = dest_language
        self.source_language = source_language
        self.detector = DoubleCopyDetector(double_copy_interval)
        self.clipboard = clipboard or PyperclipClipboard()
        self.translation_service = translation_service or TranslationService(
            dest_language=dest_language, source_language=source_language
        )
        self.enable_ui = enable_ui and tk is not None
        self._queue: "queue.Queue[TranslationPayload | Exception]" = queue.Queue()
        self._last_copied_text = ""
        self._root: Optional[tk.Tk] = None
        self._original_text_widget: Optional[tk.Text] = None
        self._translated_text_widget: Optional[tk.Text] = None
        self._detected_lang_var = tk.StringVar(value="-") if self.enable_ui else None
        self._dest_lang_var = tk.StringVar(value=dest_language) if self.enable_ui else None
        self._src_lang_var = tk.StringVar(value=source_language) if self.enable_ui else None
        self._tray = SystemTrayController(self.show_window, self.shutdown) if self.enable_ui else None
        self._closing = threading.Event()

        if self.enable_ui:
            self._setup_ui()
            if self._tray:
                self._tray.run_detached()

    # UI 構築 ----------------------------------------------------------
    def _setup_ui(self) -> None:
        if tk is None:
            raise RuntimeError("Tkinter が利用できません。")

        self._root = tk.Tk()
        self._root.title("CCTranslation")
        self._root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self._root.withdraw()
        self._root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self._root.bind("<Escape>", lambda _: self.hide_window())
        self._root.configure(bg="#1e1e1e")

        content = ttk.Frame(self._root, padding=10)
        content.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(content)
        button_frame.pack(fill=tk.X)

        ttk.Label(button_frame, text="Detected").pack(side=tk.LEFT)
        ttk.Label(button_frame, textvariable=self._detected_lang_var, width=6).pack(side=tk.LEFT, padx=5)

        toggle_button = ttk.Button(button_frame, text="Toggle", command=self.toggle_languages)
        toggle_button.pack(side=tk.LEFT, padx=5)

        self._dest_lang_var.trace_add("write", self._on_dest_var_changed)
        self._src_lang_var.trace_add("write", self._on_src_var_changed)

        dest_menu = ttk.OptionMenu(
            button_frame,
            self._dest_lang_var,
            self.dest_language,
            "ja",
            "en",
        )
        dest_menu.pack(side=tk.LEFT, padx=5)

        src_menu = ttk.OptionMenu(
            button_frame,
            self._src_lang_var,
            self.source_language,
            "auto",
            "ja",
            "en",
        )
        src_menu.pack(side=tk.LEFT, padx=5)

        text_frame = ttk.Frame(content)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        upper_frame = ttk.Frame(text_frame)
        upper_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(upper_frame, text="Original").pack(anchor=tk.W)
        self._original_text_widget = tk.Text(upper_frame, height=8, wrap=tk.WORD)
        self._original_text_widget.pack(fill=tk.BOTH, expand=True)
        self._original_text_widget.configure(state=tk.DISABLED)

        lower_frame = ttk.Frame(text_frame)
        lower_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(lower_frame, text="Translated").pack(anchor=tk.W)
        self._translated_text_widget = tk.Text(lower_frame, height=8, wrap=tk.WORD)
        self._translated_text_widget.pack(fill=tk.BOTH, expand=True)
        self._translated_text_widget.configure(state=tk.DISABLED)

        self._root.after(200, self._poll_queue)

    # UI 表示制御 ------------------------------------------------------
    def show_window(self) -> None:
        if not self.enable_ui or not self._root:
            return
        self._root.deiconify()
        self._root.lift()
        self._root.attributes("-topmost", True)
        self._root.after(100, lambda: self._root.attributes("-topmost", False))
        self._move_near_pointer()

    def hide_window(self) -> None:
        if not self.enable_ui or not self._root:
            return
        self._root.withdraw()

    def _move_near_pointer(self) -> None:
        if not self._root:
            return
        x = self._root.winfo_pointerx() - self.WINDOW_WIDTH // 2
        y = self._root.winfo_pointery() - self.WINDOW_HEIGHT // 2
        self._root.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # 翻訳処理 ----------------------------------------------------------
    def on_copy(self) -> None:
        if self.detector.register_copy():
            LOGGER.debug("Double copy detected")
            self.request_translation()

    def request_translation(self) -> None:
        text = self.clipboard.get_text()
        if not text.strip():
            LOGGER.info("クリップボードが空のため翻訳をスキップ")
            return
        if text == self._last_copied_text:
            LOGGER.info("前回と同一のテキストのため翻訳をスキップ")
            return
        self._last_copied_text = text
        worker = TranslationWorker(
            text,
            self._queue,
            self.translation_service,
            dest_language=self.dest_language,
            source_language=self.source_language,
        )
        worker.start()

    def _poll_queue(self) -> None:
        if self._closing.is_set():
            return
        try:
            item = self._queue.get_nowait()
        except queue.Empty:
            pass
        else:
            if isinstance(item, Exception):  # pragma: no cover - UI 表示経路
                if self.enable_ui and messagebox:
                    messagebox.showerror("CCTranslation", str(item))
            else:
                self._handle_translation_result(item)
        finally:
            if self.enable_ui and self._root:
                self._root.after(200, self._poll_queue)

    def _handle_translation_result(self, payload: TranslationPayload) -> None:
        if self.enable_ui:
            self._update_ui(payload)
            self.show_window()
        else:
            LOGGER.info("%s -> %s", payload.result.detected_source_language, payload.result.translated_text)

    def _update_ui(self, payload: TranslationPayload) -> None:
        if not self._root or not self._original_text_widget or not self._translated_text_widget:
            return
        self._detected_lang_var.set(payload.result.detected_source_language)
        self._set_text_widget(self._original_text_widget, payload.request_text)
        self._set_text_widget(self._translated_text_widget, payload.result.translated_text)

    @staticmethod
    def _set_text_widget(widget: tk.Text, text: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state=tk.DISABLED)

    # 言語設定 ----------------------------------------------------------
    def toggle_languages(self) -> None:
        self.dest_language, self.source_language = self.source_language, self.dest_language
        if self.enable_ui:
            self._dest_lang_var.set(self.dest_language)
            self._src_lang_var.set(self.source_language)

    def set_dest_language(self, lang: str) -> None:
        self.dest_language = lang
        if self.enable_ui:
            self._dest_lang_var.set(lang)

    def set_source_language(self, lang: str) -> None:
        self.source_language = lang
        if self.enable_ui:
            self._src_lang_var.set(lang)

    def _on_dest_var_changed(self, *_: object) -> None:
        if self.enable_ui and self._dest_lang_var is not None:
            self.dest_language = self._dest_lang_var.get()

    def _on_src_var_changed(self, *_: object) -> None:
        if self.enable_ui and self._src_lang_var is not None:
            self.source_language = self._src_lang_var.get()

    # ライフサイクル ----------------------------------------------------
    def run(self, keyboard_adapter_factory: Optional[Callable[[Callable[[], None]], object]] = None) -> None:
        adapter_factory = keyboard_adapter_factory
        if adapter_factory is None:
            from keyboard_adapter import KeyboardAdapter

            adapter_factory = KeyboardAdapter

        keyboard_adapter = adapter_factory(self.on_copy)
        try:
            if hasattr(keyboard_adapter, "is_available") and not keyboard_adapter.is_available():
                raise RuntimeError("キーボードフックが利用できません。")
            if hasattr(keyboard_adapter, "start"):
                keyboard_adapter.start()
            if self.enable_ui and self._root:
                self._root.mainloop()
            else:
                # UI が無効な場合でもキーボードフックを維持
                while True:
                    time.sleep(1)
        finally:
            if hasattr(keyboard_adapter, "stop"):
                keyboard_adapter.stop()

    def shutdown(self) -> None:
        self._closing.set()
        if self.enable_ui and self._root:
            self._root.quit()
        if self._tray:
            self._tray.stop()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CCTranslation clipboard translator")
    parser.add_argument("--dest", default="ja", help="翻訳先言語コード")
    parser.add_argument("--src", default="auto", help="翻訳元言語コード")
    parser.add_argument("--double-copy-interval", type=float, default=0.5, help="ダブルコピー判定の間隔")
    parser.add_argument("--once", action="store_true", help="単発翻訳モード")
    return parser.parse_args(argv)


def run_once(dest: str, src: str, clipboard: Optional[ClipboardInterface] = None) -> None:
    clipboard = clipboard or PyperclipClipboard()
    service = TranslationService(dest_language=dest, source_language=src)
    text = clipboard.get_text()
    if not text.strip():
        print("クリップボードが空です。", file=sys.stderr)
        return
    result = service.translate(text)
    print(f"Detected: {result.detected_source_language}")
    print(result.translated_text)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
    args = parse_args(argv)

    if args.once:
        run_once(args.dest, args.src)
        return 0

    guard = SingleInstanceGuard("CCTranslation")
    if not guard.acquire():
        print("CCTranslation は既に起動しています。", file=sys.stderr)
        return 1

    try:
        app = TranslatorApp(
            dest_language=args.dest,
            source_language=args.src,
            double_copy_interval=args.double_copy_interval,
        )
        app.run()
    except Exception as exc:
        LOGGER.exception("アプリケーションが異常終了しました")
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        guard.release()
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI エントリポイント
    raise SystemExit(main())

