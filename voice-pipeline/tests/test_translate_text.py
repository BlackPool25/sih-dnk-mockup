"""POST /translate/text — batched translate|transliterate to English (MCP-shaped contract).

Covers: single/multi-item batches (ONE mayura call), kind semantics
(transliterate→flag True, translate→flag False), line-count preservation,
per-item fallback on count mismatch, validation errors, upstream failure.
"""

import pytest
from fastapi.testclient import TestClient

import main


def test_single_item_transliterate(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            calls.append(
                (text, {"source": source, "target": target, "flag": enable_indic_transliteration})
            )
            return "Shikha"

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text",
            json={"items": [{"key": "consignee", "text": "शिखा", "kind": "transliterate"}]},
        )
    assert response.status_code == 200
    assert response.json() == {"items": [{"key": "consignee", "english": "Shikha"}]}
    # exactly ONE upstream mayura call, batched, target en-IN, transliteration ON
    assert len(calls) == 1
    assert calls[0][0] == "शिखा"
    assert calls[0][1] == {"source": "auto", "target": "en-IN", "flag": True}


def test_multi_item_batched_into_one_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            calls.append(text)
            return "Shikha\nRamesh Kumar\nNew Delhi"

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text",
            json={
                "items": [
                    {"key": "consignee", "text": "शिखा", "kind": "transliterate"},
                    {"key": "c1", "text": "रमेश कुमार", "kind": "transliterate"},
                    {"key": "city", "text": "नई दिल्ली", "kind": "translate"},
                ]
            },
        )
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"key": "consignee", "english": "Shikha"},
            {"key": "c1", "english": "Ramesh Kumar"},
            {"key": "city", "english": "New Delhi"},
        ]
    }
    # ONE call, items newline-joined in order
    assert len(calls) == 1
    assert calls[0] == "शिखा\nरमेश कुमार\nनई दिल्ली"


def test_translate_kind_uses_flag_false(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool | None] = []

    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            calls.append(enable_indic_transliteration)
            return "My name is Shikha"

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text",
            json={"items": [{"key": "note", "text": "मेरा नाम शिखा है", "kind": "translate"}]},
        )
    assert response.status_code == 200
    assert response.json() == {"items": [{"key": "note", "english": "My name is Shikha"}]}
    assert calls == [False]


def test_line_count_mismatch_falls_back_per_item(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            calls.append(text)
            # first (batched) call collapses lines; per-item calls return exact text
            return "Shikha\nRamesh Kumar" if "\n" in text else f"E:{text}"

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text",
            json={
                "items": [
                    {"key": "a", "text": "शिखा", "kind": "transliterate"},
                    {"key": "b", "text": "रमेश कुमार", "kind": "transliterate"},
                    {"key": "c", "text": "नई दिल्ली", "kind": "transliterate"},
                ]
            },
        )
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"key": "a", "english": "E:शिखा"},
            {"key": "b", "english": "E:रमेश कुमार"},
            {"key": "c", "english": "E:नई दिल्ली"},
        ]
    }
    assert len(calls) == 4  # 1 batch + 3 per-item fallback


def test_empty_items_400(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            raise AssertionError("must not be called")

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post("/translate/text", json={"items": []})
    assert response.status_code == 400
    assert "items" in response.json()["detail"]


def test_duplicate_keys_400(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            raise AssertionError("must not be called")

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text",
            json={
                "items": [
                    {"key": "dup", "text": "शिखा", "kind": "transliterate"},
                    {"key": "dup", "text": "रमेश", "kind": "transliterate"},
                ]
            },
        )
    assert response.status_code == 400
    assert "duplicate" in response.json()["detail"]


def test_empty_text_item_400(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            raise AssertionError("must not be called")

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text", json={"items": [{"key": "x", "text": "", "kind": "transliterate"}]}
        )
    assert response.status_code == 400


def test_upstream_failure_502(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.sarvam import SarvamError

    class _FakeSarvam:
        def translate(
            self,
            text: str,
            source: str = "auto",
            target: str = "hi-IN",
            enable_indic_transliteration: bool | None = None,
        ) -> str:
            raise SarvamError(500, "boom")

    monkeypatch.setattr(main, "get_sarvam_client", lambda: _FakeSarvam())
    with TestClient(main.app) as client:
        response = client.post(
            "/translate/text", json={"items": [{"key": "x", "text": "शिखा", "kind": "transliterate"}]}
        )
    assert response.status_code == 502
    assert "boom" in response.json()["detail"]
