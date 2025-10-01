"""Google 翻訳の Web API を利用する翻訳サービスモジュール。

このモジュールは、Google が公開している非公式のエンドポイント
``https://translate.googleapis.com`` を利用して簡易的な翻訳機能を
提供する。正式な Google Cloud Translation API ではないため、
商用利用や大量リクエストには適さないが、個人ユースのユーティ
リティを素早く構築する目的には十分である。

本ファイルでは `TranslationService` クラスを中心に、翻訳要求を
発行して結果を受け取るための最低限の実装を提供する。API 変更
やレートリミットに備えて例外を投げるようになっているので、呼
び出し側で適切に通知・再試行制御を行うことが望ましい。
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:  # pragma: no cover - 環境依存
    import requests
except Exception:  # pragma: no cover - 環境依存
    requests = None


LOGGER = logging.getLogger(__name__)


class TranslationError(RuntimeError):
    """翻訳処理中に発生した例外を表現する独自例外。"""


@dataclass(frozen=True)
class TranslationResult:
    """翻訳結果を格納するシンプルなデータクラス。"""

    translated_text: str
    detected_source_language: str


class TranslationService:
    """Google 翻訳 Web API を利用した翻訳クライアント。

    公式 SDK を利用せず HTTP リクエストのみで実現しているため、
    依存ライブラリは `requests` のみである。セッションは再利用
    され、複数スレッドから安全に呼び出せるようにロックを導入し
    ている。
    """

    _ENDPOINT = "https://translate.googleapis.com/translate_a/single"

    def __init__(
        self,
        dest_language: str = "ja",
        source_language: str = "auto",
        session: Optional[object] = None,
    ) -> None:
        self._dest_language = dest_language
        self._source_language = source_language
        if requests is not None:
            self._session = session or requests.Session()
        else:
            self._session = None
        self._lock = threading.Lock()

    @property
    def default_dest_language(self) -> str:
        return self._dest_language

    @property
    def default_source_language(self) -> str:
        return self._source_language

    def translate(
        self,
        text: str,
        dest_language: Optional[str] = None,
        source_language: Optional[str] = None,
    ) -> TranslationResult:
        """テキストを翻訳して結果を返す。

        Args:
            text: 翻訳したい文字列。
            dest_language: 翻訳先言語コード。未指定の場合はデフォルト。
            source_language: 翻訳元言語コード。未指定の場合はデフォルト。

        Returns:
            TranslationResult: 翻訳後のテキストと言語情報。
        """

        if not text:
            raise TranslationError("翻訳するテキストが空です。")

        params = {
            "client": "gtx",
            "sl": source_language or self._source_language,
            "tl": dest_language or self._dest_language,
            "dt": "t",
            "dj": "1",
            "source": "input",
            "q": text,
        }

        LOGGER.debug("Translation request parameters: %s", params)

        payload = self._perform_request(params)

        translated_text = "".join(sentence["trans"] for sentence in payload.get("sentences", []))
        detected_source_language = payload.get("src", params["sl"])

        if not translated_text:
            raise TranslationError("翻訳結果が空でした。")

        LOGGER.debug(
            "Translation successful: %s -> %s", detected_source_language, params["tl"]
        )

        return TranslationResult(
            translated_text=translated_text,
            detected_source_language=detected_source_language,
        )

    def _perform_request(self, params: dict) -> dict:
        if requests is not None:
            with self._lock:
                try:
                    response = self._session.get(self._ENDPOINT, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except requests.RequestException as exc:  # pragma: no cover - 例外経路
                    raise TranslationError("翻訳リクエストの送信に失敗しました。") from exc

        query = urlencode(params)
        request = Request(f"{self._ENDPOINT}?{query}", headers={"User-Agent": "CCTranslation/1.0"})
        with self._lock:
            try:
                with urlopen(request, timeout=10) as response:
                    raw = response.read()
            except (HTTPError, URLError) as exc:  # pragma: no cover - 例外経路
                raise TranslationError("翻訳リクエストの送信に失敗しました。") from exc

        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - 例外経路
            raise TranslationError("翻訳レスポンスの解析に失敗しました。") from exc

    def close(self) -> None:
        """保持しているセッションをクローズする。"""

        if self._session is not None:
            self._session.close()


__all__ = [
    "TranslationError",
    "TranslationResult",
    "TranslationService",
]

