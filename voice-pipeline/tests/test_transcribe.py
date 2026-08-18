"""POST /transcribe — Sarvam STT path, additive quality keys, empty file rejection."""

import pytest
from fastapi.testclient import TestClient

import main

WAV_BYTES = b"RIFF\x00fake-audio-bytes"


class _FakeSarvam:
    def __init__(self, transcript: str, language_probability: float | None = None) -> None:
        self.transcript = transcript
        self.language_probability = language_probability
        self.calls: list[tuple[bytes, str, str]] = []

    def transcribe_full(
        self, audio: bytes, language: str = "hi-IN", mode: str = "verbatim"
    ) -> dict[str, str | float | None]:
        self.calls.append((audio, language, mode))
        return {"transcript": self.transcript, "language_probability": self.language_probability}


def _post(client: TestClient) -> object:
    return client.post(
        "/transcribe",
        files={"file": ("voice.wav", WAV_BYTES, "audio/wav")},
        data={"language_hint": "hi"},
    )


def test_empty_file_rejected() -> None:
    with TestClient(main.app) as client:
        response = client.post(
            "/transcribe",
            files={"file": ("empty.wav", b"", "audio/wav")},
            data={"language_hint": "hi"},
        )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_sarvam_path_uses_sarvam_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSarvam("नमस्ते दुनिया", language_probability=0.9)
    monkeypatch.setattr(main, "get_sarvam_client", lambda: fake)
    with TestClient(main.app) as client:
        response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "नमस्ते दुनिया"
    assert body["language"] == "hi-IN"
    assert body["provider"] == "sarvam"
    assert body["word_count"] == 2
    assert body["low_confidence"] is False
    assert body["language_probability"] == 0.9
    assert fake.calls == [(WAV_BYTES, "hi-IN", "verbatim")]


def test_sarvam_path_omits_language_probability_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeSarvam("नमस्ते दुनिया")
    monkeypatch.setattr(main, "get_sarvam_client", lambda: fake)
    with TestClient(main.app) as client:
        response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert "language_probability" not in body
    assert body["word_count"] == 2
    assert body["low_confidence"] is False
