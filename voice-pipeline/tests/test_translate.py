"""POST /translate — Sarvam passthrough."""

import pytest
from fastapi.testclient import TestClient

import main


def test_translate_passes_through(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str]] = []

    class _FakeSarvam:
        def translate(self, text: str, source: str = "auto", target: str = "hi-IN") -> str:
            calls.append((text, source, target))
            return "नमस्ते दुनिया"

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate", json={"input": "Hello world", "source_language_code": "en-IN"}
        )
    assert response.status_code == 200
    assert response.json() == {"translated_text": "नमस्ते दुनिया"}
    assert calls == [("Hello world", "en-IN", "hi-IN")]
