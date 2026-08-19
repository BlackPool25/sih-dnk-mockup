from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.provenance import row_provenance


def test_row_provenance_returns_empty_dict_for_object_without_fields() -> None:
    assert row_provenance(object()) == {}


def test_row_provenance_includes_present_fields() -> None:
    row = SimpleNamespace(
        source_url="https://example.test/source",
        source_level="L1",
        confidence="high",
        is_estimate=False,
    )

    assert row_provenance(row) == {
        "source_url": "https://example.test/source",
        "source_level": "L1",
        "confidence": "high",
        "is_estimate": False,
    }


def test_row_provenance_omits_none_fields() -> None:
    row = SimpleNamespace(
        source_url="https://example.test/source",
        source_level="L2",
        confidence="moderate",
        is_estimate=True,
        effective_from=None,
        effective_to=None,
        verified_at=None,
    )

    provenance = row_provenance(row)

    assert "effective_from" not in provenance
    assert "effective_to" not in provenance
    assert "verified_at" not in provenance


def test_row_provenance_serializes_dates() -> None:
    row = SimpleNamespace(
        source_url="https://example.test/source",
        source_level="L1",
        confidence="high",
        is_estimate=False,
        effective_from=date(2026, 2, 6),
        effective_to=date(2026, 12, 31),
        verified_at=datetime(2026, 8, 12, 10, 30, tzinfo=timezone.utc),
    )

    provenance = row_provenance(row)

    assert provenance["effective_from"] == "2026-02-06"
    assert provenance["effective_to"] == "2026-12-31"
    assert provenance["verified_at"] == "2026-08-12T10:30:00+00:00"