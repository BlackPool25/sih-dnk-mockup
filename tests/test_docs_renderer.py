"""Tests for the todo-11 document generation pipeline.

These hit the LIVE seeded DB (no fixtures — the container must be up), like
the rest of the suite.  Every test that INSERTs a ``documents`` row cleans it
up afterwards (rows are immutable — tests must not pollute the chain).

Covers:
- happy path: ``render()`` on a complete DocumentData -> Document with a
  64-hex sha256 checksum, PBE_IV.
- failures: unknown doc_type -> ValueError; INCOMPLETE DocumentData ->
  ValidationError raised BEFORE WeasyPrint, NO PDF, documents count unchanged.
- CLI: ``--preview`` without ``--yes`` never calls the renderer;
  ``--country ZZ`` / ``--country unknown`` exit non-zero with an error.
- USER REQUIREMENTS (2026-08-09): the preview carries the hi/kn confirm
  labels; the form HTML/PDF contains NO Devanagari/Kannada text;
  ``missing_required`` gates render.
- immutable versioning: re-render -> version 2, supersedes_doc_id = 1, count
  increments, no row overwritten; different content -> different checksum.
"""

import hashlib
import re
import shutil
import subprocess

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Document
from app.schemas.shipment import Shipment
from app.services.docs.__main__ import main as docs_cli_main
from app.services.docs.document import build_document_data
from app.services.docs.renderer import build_html, build_preview, render
from app.services.validate import validate_shipment

# Devanagari (U+0900..U+097F) and Kannada (U+0C80..U+0CFF) blocks — the
# bilingual scripts that may appear ONLY in the preview/UI, never in the form.
_DEVANAGARI_OR_KANNADA = re.compile(r"[\u0900-\u097F\u0C80-\u0CFF]")


# --- helpers -----------------------------------------------------------------


def _validated_shipment() -> Shipment:
    """A complete, validated Shipment (embroidered-home-textiles -> US)."""
    return validate_shipment(
        Shipment(
            product_category="embroidered-home-textiles",
            quantity=8,
            weight_grams=400,
            destination_country="US",
            confidence="high",
        )
    )


def _complete_data():
    """A complete DocumentData from REAL DB lookups (missing_required == [])."""
    return build_document_data(_validated_shipment(), "PBE_IV")


def _doc_count(doc_type: str) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.doc_type == doc_type)
        )


def _max_version(doc_type: str) -> int:
    with SessionLocal() as session:
        return (
            session.scalar(
                select(func.max(Document.version)).where(Document.doc_type == doc_type)
            )
            or 0
        )


@pytest.fixture
def clean_documents():
    """Delete every ``documents`` row created during the test."""
    with SessionLocal() as session:
        before = session.scalar(select(func.max(Document.id))) or 0
    yield
    with SessionLocal() as session:
        rows = session.scalars(
            select(Document).where(Document.id > before).order_by(Document.id.desc())
        ).all()
        # Break the self-FK supersedes chain first, then delete (newest first).
        for row in rows:
            row.supersedes_doc_id = None
        session.flush()
        for row in rows:
            session.delete(row)
        session.commit()


# --- happy path --------------------------------------------------------------


def test_render_happy_returns_document_with_checksum(tmp_path, clean_documents):
    """A complete DocumentData renders to a Document with a 64-hex sha256
    checksum and doc_type PBE_IV — the next version in the chain."""
    data = _complete_data()
    assert data.form_type == "PBE_IV"
    out = tmp_path / "pbe_sample.pdf"
    before = _max_version("PBE_IV")
    doc = render(data, "PBE_IV", out_path=out)
    assert doc.doc_type == "PBE_IV"
    assert doc.version == before + 1
    assert re.fullmatch(r"[0-9a-f]{64}", doc.checksum)
    assert out.exists() and out.stat().st_size > 0
    assert doc.checksum == hashlib.sha256(out.read_bytes()).hexdigest()
    assert doc.file_path == str(out)


# --- failure paths -----------------------------------------------------------


def test_render_unknown_doc_type_raises(tmp_path, clean_documents):
    data = _complete_data()
    with pytest.raises(ValueError, match="unknown doc_type"):
        render(data, "BOGUS", out_path=tmp_path / "x.pdf")


def test_render_form_type_mismatch_raises(tmp_path, clean_documents):
    data = _complete_data()  # form_type == PBE_IV
    with pytest.raises(ValueError, match="does not match"):
        render(data, "CN22", out_path=tmp_path / "x.pdf")


class _BoomWeasyPrint:
    """write_pdf raises — proves the renderer never reached WeasyPrint."""

    def __init__(self, *args, **kwargs):
        del args, kwargs

    def write_pdf(self, *args, **kwargs):
        del args, kwargs
        raise AssertionError("WeasyPrint was called for an incomplete document")


def _incomplete_data():
    """A DocumentData whose required pbe_field_schemas fields are NOT all
    satisfied: destination 'unknown' means consignee_details is missing."""
    return _complete_data().model_copy(update={"destination_country": "unknown"})


def test_render_incomplete_raises_before_weasyprint_writes_nothing(
    tmp_path, monkeypatch, clean_documents
):
    monkeypatch.setattr("app.services.docs.renderer.weasyprint.HTML", _BoomWeasyPrint)
    before = _doc_count("PBE_IV")
    out = tmp_path / "never.pdf"
    with pytest.raises(ValidationError):
        render(_incomplete_data(), "PBE_IV", out_path=out)
    # USER REQUIREMENT: missing_required gates render — no PDF, no row.
    assert not out.exists()
    assert _doc_count("PBE_IV") == before


def test_missing_required_error_lists_pbe_field(tmp_path, clean_documents):
    """The ValidationError names the missing pbe_field_schemas field."""
    with pytest.raises(ValidationError) as excinfo:
        render(_incomplete_data(), "PBE_IV", out_path=tmp_path / "x.pdf")
    text = str(excinfo.value)
    assert "consignee_details" in text
    assert "required" in text.lower()


# --- CLI: preview gate -------------------------------------------------------


def test_preview_without_yes_does_not_call_renderer(capsys, monkeypatch):
    def boom(*args, **kwargs):
        del args, kwargs
        raise AssertionError("render() was called without --yes confirmation")

    monkeypatch.setattr("app.services.docs.__main__.render", boom)
    rc = docs_cli_main(
        [
            "render",
            "--category",
            "embroidered-home-textiles",
            "--qty",
            "8",
            "--weight-g",
            "400",
            "--country",
            "US",
            "--form",
            "PBE_IV",
            "--preview",
        ]
    )
    assert rc == 1  # confirm required
    out = capsys.readouterr()
    assert "confirm required" in out.err
    # USER REQUIREMENT: the preview carries a hi/kn confirm label.
    assert "कृपया" in out.out or "ದಯವಿಟ್ಟು" in out.out


def test_preview_with_yes_renders(tmp_path, capsys, clean_documents):
    out = tmp_path / "preview_yes.pdf"
    rc = docs_cli_main(
        [
            "render",
            "--category",
            "embroidered-home-textiles",
            "--qty",
            "8",
            "--weight-g",
            "400",
            "--country",
            "US",
            "--form",
            "PBE_IV",
            "--preview",
            "--yes",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()
    printed = capsys.readouterr().out
    assert "document id:" in printed
    assert "कृपया" in printed  # preview still shown before rendering


def test_cli_unknown_country_zz_rejected(tmp_path, capsys):
    """--country ZZ: non-zero exit + error + no PDF written."""
    out = tmp_path / "zz.pdf"
    with pytest.raises(SystemExit) as excinfo:
        docs_cli_main(
            [
                "render",
                "--category",
                "embroidered-home-textiles",
                "--qty",
                "8",
                "--weight-g",
                "400",
                "--country",
                "ZZ",
                "--form",
                "PBE_IV",
                "--out",
                str(out),
            ]
        )
    assert excinfo.value.code != 0
    assert "error" in capsys.readouterr().err
    assert not out.exists()


def test_cli_unknown_country_lists_missing_pbe_fields(capsys):
    """Completeness gate: 'unknown' destination exits non-zero listing the
    missing pbe_field_schemas fields (consignee_details)."""
    with pytest.raises(SystemExit) as excinfo:
        docs_cli_main(
            [
                "render",
                "--category",
                "embroidered-home-textiles",
                "--qty",
                "8",
                "--weight-g",
                "400",
                "--country",
                "unknown",
                "--form",
                "PBE_IV",
            ]
        )
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "consignee_details" in err
    assert "required fields missing" in err


# --- USER REQUIREMENTS: English form, bilingual preview ---------------------


def test_preview_contains_hi_kn_confirm_labels():
    """The preview (UI-only surface) carries labels.confirm.hi / .kn."""
    preview = build_preview(_complete_data())
    assert "कृपया पुष्टि करें" in preview  # labels.confirm.hi
    assert "ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ" in preview  # labels.confirm.kn


def test_form_html_is_english_only():
    """The rendered form HTML contains NO Devanagari/Kannada text, and does
    carry English content (form title + a pbe_field_schemas label)."""
    html = build_html(_complete_data(), "PBE_IV")
    assert not _DEVANAGARI_OR_KANNADA.search(html)
    assert "PBE" in html
    assert "Customs" in html  # from the CTH label in pbe_field_schemas


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext missing")
def test_form_pdf_is_english_only(tmp_path, clean_documents):
    out = tmp_path / "english.pdf"
    doc = render(_complete_data(), "PBE_IV", out_path=out)
    text = subprocess.run(
        ["pdftotext", str(out), "-"], check=True, capture_output=True, text=True
    ).stdout
    assert not _DEVANAGARI_OR_KANNADA.search(text)
    assert doc.doc_type == "PBE_IV"
    assert re.search(r"630[24]", text)  # HS code from the DB is present
    assert re.search(r"PBE|Customs|cushion", text, re.IGNORECASE)


# --- immutable versioning ----------------------------------------------------


def test_rerender_increments_version_no_overwrite(tmp_path, clean_documents):
    """Same CLI input twice -> the second version supersedes the first; the
    first row is untouched and the count increments (never an UPDATE)."""
    data = _complete_data()
    before = _max_version("PBE_IV")
    count_before = _doc_count("PBE_IV")
    doc1 = render(data, "PBE_IV", out_path=tmp_path / "v1.pdf")
    doc2 = render(data, "PBE_IV", out_path=tmp_path / "v2.pdf")
    assert doc1.version == before + 1
    assert doc2.version == before + 2
    assert doc2.supersedes_doc_id == doc1.id
    assert _doc_count("PBE_IV") == count_before + 2
    with SessionLocal() as session:
        row1 = session.get(Document, doc1.id)
    assert row1.version == doc1.version  # immutable — never updated in place


def test_checksum_differs_with_different_content(tmp_path, clean_documents):
    """--qty 9 renders a different checksum than the qty-8 document."""
    qty8 = _complete_data()
    qty9 = _complete_data().model_copy(update={"quantity": 9})
    doc8 = render(qty8, "PBE_IV", out_path=tmp_path / "q8.pdf")
    doc9 = render(qty9, "PBE_IV", out_path=tmp_path / "q9.pdf")
    assert doc8.checksum != doc9.checksum
