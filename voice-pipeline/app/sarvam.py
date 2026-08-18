"""Sarvam AI API client — STT, TTS, and translate with retry on transient errors."""

import base64
import os
import time
from collections.abc import Callable

import httpx

BASE_URL = "https://api.sarvam.ai"
STT_MODEL = "saaras:v3"
TTS_MODEL = "bulbul:v2"
TRANSLATE_MODEL = "mayura:v1"
MAX_ATTEMPTS = 3
RETRY_BASE_SECONDS = 1.0
RETRYABLE_STATUSES = frozenset({429, 500, 503})


class SarvamError(ValueError):
    """Upstream API rejected the request; message carries the API's own detail."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Sarvam API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message


def _error_text(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        for key in ("message", "detail"):
            if body.get(key):
                return str(body[key])
    return f"HTTP {response.status_code}: {response.text[:200]}"


class SarvamClient:
    """Thin wrapper over the Sarvam AI REST API (https://api.sarvam.ai)."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"api-subscription-key": api_key or os.getenv("SARVAM_API_KEY", "")},
            timeout=timeout,
            transport=transport,
        )

    def transcribe_full(
        self, audio: bytes, language: str = "hi-IN", mode: str = "verbatim"
    ) -> dict[str, str | float | None]:
        response = self._request(
            lambda: self._client.post(
                "/speech-to-text",
                files={"file": ("audio.wav", audio, "audio/wav")},
                data={"model": STT_MODEL, "mode": mode, "language_code": language},
            )
        )
        body = response.json()
        return {
            "transcript": str(body["transcript"]),
            "language_probability": body.get("language_probability"),
        }

    def transcribe(self, audio: bytes, language: str = "hi-IN", mode: str = "verbatim") -> str:
        return str(self.transcribe_full(audio, language, mode)["transcript"])

    def synthesize(self, text: str, language: str = "hi-IN", speaker: str = "anushka") -> bytes:
        response = self._request(
            lambda: self._client.post(
                "/text-to-speech",
                json={
                    "text": text,
                    "language_code": language,
                    "model": TTS_MODEL,
                    "speaker": speaker,
                    "speech_sample_rate": 24000,
                    "output_audio_codec": "wav",
                },
            )
        )
        return base64.b64decode(response.json()["audios"][0])

    def translate(self, text: str, source: str = "auto", target: str = "hi-IN") -> str:
        response = self._request(
            lambda: self._client.post(
                "/translate",
                json={
                    "input": text,
                    "source_language_code": source,
                    "target_language_code": target,
                    "model": TRANSLATE_MODEL,
                },
            )
        )
        return str(response.json()["translated_text"])

    def _request(self, send: Callable[[], httpx.Response]) -> httpx.Response:
        attempts = 0
        while True:
            attempts += 1
            response = send()
            if response.status_code in RETRYABLE_STATUSES and attempts < MAX_ATTEMPTS:
                time.sleep(RETRY_BASE_SECONDS * (2 ** (attempts - 1)))
                continue
            if response.status_code >= 400:
                raise SarvamError(response.status_code, _error_text(response))
            return response


_sarvam_client: SarvamClient | None = None


def get_sarvam_client() -> SarvamClient:
    """Return the process-wide SarvamClient, creating it on first use."""
    global _sarvam_client
    if _sarvam_client is None:
        _sarvam_client = SarvamClient()
    return _sarvam_client
