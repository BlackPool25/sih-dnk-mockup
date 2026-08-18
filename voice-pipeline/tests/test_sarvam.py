"""SarvamClient — request shapes, transcribe_full, retry on 429, error mapping."""

import base64
import json

import httpx
import pytest

from app import sarvam


def _client(handler, api_key: str = "test-key") -> sarvam.SarvamClient:
    return sarvam.SarvamClient(api_key=api_key, transport=httpx.MockTransport(handler))


def test_transcribe_multipart_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/speech-to-text"
        assert request.headers["api-subscription-key"] == "test-key"
        assert request.headers["content-type"].startswith("multipart/form-data")
        body = request.read()
        assert b'name="model"' in body and b"saaras:v3" in body
        assert b'name="mode"' in body and b"verbatim" in body
        assert b'name="language_code"' in body and b"hi-IN" in body
        assert b'filename="audio.wav"' in body
        assert b"fake-audio" in body
        return httpx.Response(
            200,
            json={
                "request_id": "r1",
                "transcript": "नमस्ते दुनिया",
                "language_code": "hi-IN",
                "language_probability": 0.99,
            },
        )

    client = _client(handler)
    assert client.transcribe(b"fake-audio") == "नमस्ते दुनिया"


def test_transcribe_full_returns_language_probability() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "request_id": "r1",
                "transcript": "नमस्ते दुनिया",
                "language_code": "hi-IN",
                "language_probability": 0.898,
            },
        )

    client = _client(handler)
    assert client.transcribe_full(b"fake-audio") == {
        "transcript": "नमस्ते दुनिया",
        "language_probability": 0.898,
    }


def test_transcribe_full_language_probability_none_when_absent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"request_id": "r2", "transcript": "नमस्ते", "language_code": "hi-IN"},
        )

    client = _client(handler)
    assert client.transcribe_full(b"fake-audio") == {
        "transcript": "नमस्ते",
        "language_probability": None,
    }


def test_synthesize_base64_roundtrip() -> None:
    wav = b"RIFF\x00\x01\x02fake-wav"
    encoded = base64.b64encode(wav).decode()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/text-to-speech"
        assert json.loads(request.read()) == {
            "text": "नमस्ते",
            "language_code": "hi-IN",
            "model": "bulbul:v2",
            "speaker": "anushka",
            "speech_sample_rate": 24000,
            "output_audio_codec": "wav",
        }
        return httpx.Response(200, json={"request_id": "r2", "audios": [encoded]})

    client = _client(handler)
    assert client.synthesize("नमस्ते") == wav


def test_translate_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/translate"
        assert json.loads(request.read()) == {
            "input": "Hello world",
            "source_language_code": "en-IN",
            "target_language_code": "hi-IN",
            "model": "mayura:v1",
        }
        return httpx.Response(200, json={"request_id": "r3", "translated_text": "नमस्ते दुनिया"})

    client = _client(handler)
    assert client.translate("Hello world", source="en-IN") == "नमस्ते दुनिया"


def test_retries_429_then_succeeds() -> None:
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        if counter["n"] == 1:
            return httpx.Response(429, json={"error": {"code": "rate_limit_exceeded_error", "message": "slow down"}})
        return httpx.Response(200, json={"request_id": "r4", "transcript": "ok"})

    client = _client(handler)
    assert client.transcribe(b"audio") == "ok"
    assert counter["n"] == 2


def test_403_raises_value_error_with_api_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"code": "invalid_api_key_error", "message": "API key is invalid"}})

    client = _client(handler, api_key="bad-key")
    with pytest.raises(ValueError) as excinfo:
        client.transcribe(b"audio")
    assert "API key is invalid" in str(excinfo.value)
