"""Guidance toggle + typo-tolerant + per-field Sarvam hints tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _get(field: str, hindi_help: bool) -> dict[str, object]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/guidance/signup", params={"field": field, "hindi_help": str(hindi_help).lower()})
        assert r.status_code == 200, r.text
        return r.json()  # type: ignore[no-any-return]


@pytest.mark.asyncio
async def test_explicit_toggle_false_returns_english() -> None:
    data = await _get("pan", False)
    assert data["hindi_help"] is False
    assert data["tts_url"] is None
    assert "PAN" in str(data["simple_words"])
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["side_by_side"] is None


@pytest.mark.asyncio
async def test_explicit_toggle_true_returns_hindi() -> None:
    data = await _get("pan", True)
    assert data["hindi_help"] is True
    assert "PAN" in str(data["simple_words"])  # Hinglish contains PAN
    assert "अक्षर" in str(data["simple_words"]) or "PAN" in str(data["hint"])
    assert str(data["tts_url"]).startswith("mock://bulbul/pan")
    assert data["mocked"] is True


@pytest.mark.asyncio
async def test_iec_typo_tolerant_iecc() -> None:
    data = await _get("iecc", True)
    assert data["field"] == "iec"
    assert "IEC" in str(data["simple_words"])
    assert str(data["tts_url"]).startswith("mock://bulbul/iec")


@pytest.mark.asyncio
async def test_iec_typo_tolerant_via_levenshtein() -> None:
    # 'iec' with extra char not in alias map triggers Levenshtein
    data = await _get("iecs", True)
    assert data["field"] == "iec"


@pytest.mark.asyncio
async def test_every_field_hint_via_sarvam() -> None:
    fields = ["pan", "iec", "ad_code", "icegate", "bank", "gstin", "udyam", "rcmc"]
    for f in fields:
        data = await _get(f, True)
        assert data["field"] == f
        assert isinstance(data["hint"], str) and len(str(data["hint"])) > 0
        assert isinstance(data["simple_words"], str) and len(str(data["simple_words"])) > 0
        assert str(data["tts_url"]) == f"mock://bulbul/{f}", f"field {f} tts mismatch: {data['tts_url']}"
        assert data["mocked"] is True
        assert data["verification_mode"] == "mock"


@pytest.mark.asyncio
async def test_every_field_english_no_tts() -> None:
    for f in ["pan", "iec", "bank", "gstin"]:
        data = await _get(f, False)
        assert data["tts_url"] is None


@pytest.mark.asyncio
async def test_gstin_skippable() -> None:
    data = await _get("gstin", True)
    assert data["required"] is False
    assert data["skippable"] is True
    assert "बाद में" in str(data["simple_words"])
    assert "बाद में" in str(data["hint"]) or "skip" in str(data["hint"]).lower()


@pytest.mark.asyncio
async def test_udyam_rcmc_skippable() -> None:
    for f in ["udyam", "rcmc"]:
        data = await _get(f, True)
        assert data["required"] is False
        assert data["skippable"] is True
        assert "बाद में" in str(data["simple_words"])


@pytest.mark.asyncio
async def test_upfront_required_not_skippable() -> None:
    for f in ["pan", "iec", "ad_code", "icegate", "bank"]:
        data = await _get(f, True)
        assert data["required"] is True
        assert data["skippable"] is False


@pytest.mark.asyncio
async def test_upfront_order() -> None:
    data = await _get("pan", True)
    assert data["upfront_order"] == ["pan", "iec", "ad_code", "icegate", "bank"]


@pytest.mark.asyncio
async def test_ad_code_hint_contains_bank() -> None:
    data = await _get("ad_code", True)
    assert "14" in str(data["simple_words"])
    assert "बैंक" in str(data["simple_words"])
