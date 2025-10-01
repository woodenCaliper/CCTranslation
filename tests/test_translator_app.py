import queue
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from translator_app import DoubleCopyDetector, DummyClipboard, TranslationPayload, TranslatorApp


class DummyService:
    def __init__(self) -> None:
        self.calls = []

    def translate(self, text: str, dest_language: str = "ja", source_language: str = "auto"):
        self.calls.append((text, dest_language, source_language))

        class Result:
            translated_text = text.upper()
            detected_source_language = source_language

        return Result()


def test_double_copy_detector_triggers_within_interval():
    detector = DoubleCopyDetector(interval=0.5)
    now = time.monotonic()
    assert not detector.register_copy(timestamp=now)
    assert detector.register_copy(timestamp=now + 0.2)
    assert not detector.register_copy(timestamp=now + 1.0)


def test_translation_requested_only_for_new_text(monkeypatch):
    clipboard = DummyClipboard()
    clipboard.set_text("hello")
    service = DummyService()

    app = TranslatorApp(
        dest_language="ja",
        source_language="auto",
        double_copy_interval=0.5,
        clipboard=clipboard,
        translation_service=service,
        enable_ui=False,
    )

    app.request_translation()
    assert service.calls == [("hello", "ja", "auto")]

    # 同じテキストはスキップ
    app.request_translation()
    assert service.calls == [("hello", "ja", "auto")]

    # 空文字は翻訳しない
    clipboard.set_text("\n\n")
    app.request_translation()
    assert service.calls == [("hello", "ja", "auto")]

    # 新しいテキストは翻訳される
    clipboard.set_text("world")
    app.request_translation()
    assert service.calls[-1] == ("world", "ja", "auto")


def test_handle_translation_result_updates_queue(monkeypatch, caplog):
    clipboard = DummyClipboard()
    clipboard.set_text("hello")
    service = DummyService()

    app = TranslatorApp(
        clipboard=clipboard,
        translation_service=service,
        enable_ui=False,
    )

    app.request_translation()

    # バックグラウンドスレッドが完了するまで待機
    deadline = time.time() + 2
    while time.time() < deadline:
        try:
            payload = app._queue.get_nowait()
            assert isinstance(payload, TranslationPayload)
            break
        except queue.Empty:
            time.sleep(0.05)
    else:
        pytest.fail("タイムアウトしました")

