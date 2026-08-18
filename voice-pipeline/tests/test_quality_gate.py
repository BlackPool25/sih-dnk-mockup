"""Additive quality-gate keys on /transcribe — low-confidence detection for garbled STT.

The acceptance contract: a 1-word garbled transcript (e.g. "जामुली") must produce
low_confidence True so the chat re-prompts instead of accepting garbage. Sarvam's
STT returns no segment-level confidence, so the gate is transcript-based.
"""

import pytest
from fastapi.testclient import TestClient

import main

WAV_BYTES = b"RIFF\x00fake-audio-bytes"


class _FakeSarvam:
    def __init__(self, transcript: str, language_probability: float | None = None) -> None:
        self._transcript = transcript
        self._language_probability = language_probability

    def transcribe_full(
        self, audio: bytes, language: str = "hi-IN", mode: str = "verbatim"
    ) -> dict[str, str | float | None]:
        return {"transcript": self._transcript, "language_probability": self._language_probability}


def _client_with_transcript(monkeypatch: pytest.MonkeyPatch, transcript: str) -> TestClient:
    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam(transcript))
    return TestClient(main.app)


def _post(client: TestClient) -> object:
    return client.post(
        "/transcribe",
        files={"file": ("voice.wav", WAV_BYTES, "audio/wav")},
        data={"language_hint": "hi"},
    )


def test_garbled_single_word_flagged_low_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    with _client_with_transcript(monkeypatch, "जामुली") as client:
        response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "जामुली"
    assert body["word_count"] == 1
    assert body["low_confidence"] is True


def test_normal_two_token_transcript_low_confidence_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _client_with_transcript(monkeypatch, "नमस्ते दुनिया") as client:
        response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "नमस्ते दुनिया"
    assert body["word_count"] == 2
    assert body["low_confidence"] is False


def test_empty_transcript_flagged_low_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    with _client_with_transcript(monkeypatch, "") as client:
        response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == ""
    assert body["word_count"] == 0
    assert body["low_confidence"] is True
