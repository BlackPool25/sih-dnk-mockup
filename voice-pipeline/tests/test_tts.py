"""POST /tts — Sarvam synthesis and the length guard."""

import pytest
from fastapi.testclient import TestClient

import main

FAKE_WAV = b"RIFFfake-wav-bytes"


def test_tts_text_too_long_returns_400() -> None:
    with TestClient(main.app) as client:
        response = client.post("/tts", json={"text": "न" * 401})
    assert response.status_code == 400
    assert "400" in response.json()["detail"]


def test_tts_sarvam_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str]] = []

    class _FakeSarvam:
        def synthesize(self, text: str, language: str = "hi-IN", speaker: str = "anushka") -> bytes:
            calls.append((text, language, speaker))
            return FAKE_WAV

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post("/tts", json={"text": "नमस्ते"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == FAKE_WAV
    assert calls == [("नमस्ते", "hi-IN", "anushka")]
