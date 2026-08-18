"""Tests for the todo-11 document generation pipeline.

These hit the LIVE seeded DB (no fixtures — the container must be up), like
the rest of the suite.  Every test that INSERTs a ``documents`` row cleans it
up afterwards (rows are immutable — tests must not pollute the chain).

Covers:
- happy path: ``render()`` on a complete DocumentData -> Document with a
  64-hex sha256 checksum, PBE_IV (IEC+GSTIN supplied for the todo-14 gates).
- failures: unknown doc_type -> ValueError; INCOMPLETE DocumentData ->
  ValidationError raised BEFORE WeasyPrint, NO PDF, documents count unchanged.
- CLI: ``--preview`` without ``--yes`` never calls the renderer;
  ``--country ZZ`` / ``--country unknown`` exit non-zero with an error.
- USER REQUIREMENTS (2026-08-09): the preview carries the hi/kn confirm
  labels; the form HTML/PDF contains NO Devanagari/Kannada text;
  ``missing_required`` gates render.
- immutable versioning: re-render -> version 2, supersedes_doc_id = 1, count
  increments, no row overwritten; different content -> different checksum.

(The todo-14 official filling rules themselves are tested in
``tests/test_validate_rules.py``.)
"""

import hashlib
import re
import shutil
import subprocess
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models import Document
from app.models.order import Order, OrderStatus
from app.schemas.shipment import Shipment
from app.services.docs.__main__ import main as docs_cli_main
from app.services.docs.cli_fields import (
    DEDICATED_FLAGS,
    field_flag_name,
    pbe_field_specs,
)
from app.services.docs.document import SenderBlock, build_document_data
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
    """A complete DocumentData from REAL DB lookups (missing_required == []).

    IEC + GSTIN are supplied so the todo-14 DGFT/KYC filling-rule gate passes;
    the same pair is passed via ``--iec``/``--gstin`` in the CLI tests.
    Consignee + declared value are supplied so the wave-2 completeness gate
    (ALL 7 required fields incl. assessable_value) also passes.
    """
    return build_document_data(
        _validated_shipment(),
        "PBE_IV",
        iec="IN1234567890",
        gstin="29ABCDE1234F1Z5",
        value_minor=200000,
        consignee="Jane Doe, 123 Main St",
    )


def _doc_count(doc_type: str) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.count()).select_from(Document).where(Document.doc_type == doc_type)
        )


def _max_version(doc_type: str) -> int:
    with SessionLocal() as session:
        return (
            session.scalar(select(func.max(Document.version)).where(Document.doc_type == doc_type))
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


def test_render_with_order_sets_document_order_id(tmp_path, clean_documents) -> None:
    """Rendering with an Order writes order_id on the new Document row."""
    order_id = uuid.uuid4()
    with SessionLocal.begin() as session:
        session.add(
            Order(
                id=order_id,
                seller_id=uuid.UUID("dc777c25-9f68-47d4-ba6b-959a14387d90"),
                buyer_id=uuid.UUID("197e1aa3-8799-404d-b983-111b2108dd1e"),
                status=OrderStatus.quote_accepted,
            )
        )
    with SessionLocal() as session:
        order = session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.line_items))
        ).scalar_one()
        doc = render(
            _complete_data(), "PBE_IV", out_path=tmp_path / "ordered.pdf", order=order
        )
    assert doc.order_id == order_id
    with SessionLocal.begin() as session:
        row = session.get(Order, order_id)
        if row is not None:
            session.delete(row)


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
    satisfied: consignee_details is removed from field_values (so it resolves
    to "—" and is reported missing by the wave-2 completeness gate)."""
    complete = _complete_data()
    return complete.model_copy(
        update={
            "destination_country": "unknown",
            "consignee": None,
            "field_values": {
                k: v for k, v in complete.field_values.items() if k != "consignee_details"
            },
        }
    )


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
            "--iec",
            "IN1234567890",
            "--gstin",
            "29ABCDE1234F1Z5",
            "--value-minor",
            "200000",
            "--consignee",
            "Jane Doe, 123 Main St",
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
            "--iec",
            "IN1234567890",
            "--gstin",
            "29ABCDE1234F1Z5",
            "--value-minor",
            "200000",
            "--consignee",
            "Jane Doe, 123 Main St",
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


def test_cli_unknown_country_rejected_at_build(capsys):
    """'unknown' destination passes validate_shipment (the sentinel) but the
    build fails with the quote_lane LookupError — exit non-zero, no PDF."""
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
    assert "lane for country 'unknown'" in capsys.readouterr().err


# --- wave 4: DB-driven auto-generated CLI flags (F5 / R3) --------------------


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext missing")
def test_cli_auto_flag_renders(tmp_path, clean_documents):
    """Auto-generated flags reach the rendered form: exporter/state/decl/scheme."""
    out = tmp_path / "auto.pdf"
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
            "--iec",
            "IN1234567890",
            "--gstin",
            "29ABCDE1234F1Z5",
            "--value-minor",
            "200000",
            "--consignee",
            "Jane Doe",
            "--exporter-name",
            "Acme Exporters",
            "--state-code",
            "29",
            "--decl-drawback",
            "Yes",
            "--scheme-code",
            "drawback",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    text = subprocess.run(
        ["pdftotext", str(out), "-"], check=True, capture_output=True, text=True
    ).stdout
    assert "Acme Exporters" in text
    assert "29" in text
    assert "[X] Yes" in text
    assert "drawback" in text


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext missing")
def test_cli_money_minor_units(tmp_path, clean_documents):
    """Money auto-flags take INR minor units and render with the ₹ format."""
    out = tmp_path / "money.pdf"
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
            "--iec",
            "IN1234567890",
            "--gstin",
            "29ABCDE1234F1Z5",
            "--value-minor",
            "200000",
            "--consignee",
            "Jane Doe",
            "--export-duty-amount-minor",
            "50000",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    text = subprocess.run(
        ["pdftotext", str(out), "-"], check=True, capture_output=True, text=True
    ).stdout
    assert "₹500.00" in text


def test_cli_net_weight_flag_reachable(tmp_path, capsys, clean_documents):
    """F5: the gross≤110%-of-net rule is now reachable via --net-weight."""
    out = tmp_path / "never.pdf"
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
                "US",
                "--form",
                "PBE_IV",
                "--iec",
                "IN1234567890",
                "--gstin",
                "29ABCDE1234F1Z5",
                "--value-minor",
                "200000",
                "--consignee",
                "Jane Doe",
                "--net-weight",
                "300",
                "--out",
                str(out),
            ]
        )
    assert excinfo.value.code != 0
    assert "gross weight exceeds 110% of net weight" in capsys.readouterr().err
    assert not out.exists()


def test_cli_auto_flags_no_collision():
    """Auto flags never collide with the legacy or dedicated flag names."""
    legacy = {
        "--category",
        "--qty",
        "--weight-g",
        "--country",
        "--form",
        "--out",
        "--preview",
        "--yes",
        "--ask-optional",
        "--consignee",
        "--value-minor",
        "--iec",
        "--gstin",
    }
    auto = {field_flag_name(s) for s in pbe_field_specs()}
    assert auto.isdisjoint(legacy | DEDICATED_FLAGS)
    dests = [s["field_key"] for s in pbe_field_specs()]
    assert len(dests) == len(set(dests))


# --- USER REQUIREMENTS: English form, bilingual preview ---------------------


def test_preview_contains_hi_kn_confirm_labels():
    """The preview (UI-only surface) carries labels.confirm.hi / .kn."""
    preview = build_preview(_complete_data())
    assert "कृपया पुष्टि करें" in preview  # labels.confirm.hi
    assert "ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ" in preview  # labels.confirm.kn


def test_form_html_is_english_only():
    """The rendered form HTML contains NO Devanagari/Kannada text, and carries
    the OFFICIAL Notification 07/2026-Customs column labels verbatim."""
    html = build_html(_complete_data(), "PBE_IV")
    assert not _DEVANAGARI_OR_KANNADA.search(html)
    assert "PBE" in html
    # OFFICIAL FORMAT: Notification 07/2026-Customs column labels verbatim.
    assert "Assessable value" in html
    assert "RITC code/ITC\u2011HS code" in html  # U+2011 non-breaking hyphen (R5)
    assert "Nature of contract (CIF/CF/C&F/FOB)" in html
    assert "Customs" in html  # e.g. "Customs Broker License No." / "Customs Act, 1962"


def test_cn_sender_block_fillable():
    """The CN22 sender block is fillable from SenderBlock — not hardcoded '—'."""
    data = _complete_data().model_copy(
        update={
            "form_type": "CN22",
            "sender": SenderBlock(
                name_address="Acme Exports, Delhi",
                sender_ref="IOSS0001",
                non_delivery="return",
                num_invoices="2",
            ),
        }
    )
    html = build_html(data, "CN22")
    assert "Acme Exports, Delhi" in html
    assert "IOSS0001" in html
    assert "return" in html
    assert ">2<" in html


def test_declaration_box_marks_chosen_value():
    """The Drawback declaration row marks its chosen option with X; the others
    stay unchecked (the box shows the OPTION, not the '—' placeholder)."""
    data = _complete_data().model_copy(
        update={
            "field_values": {
                **_complete_data().field_values,
                "decl.drawback": "Yes",
            }
        }
    )
    html = build_html(data, "PBE_IV")
    m = re.search(r"claim Drawback.*?<td class=\"decl-box\">(.*?)</td>", html, re.DOTALL)
    assert m is not None, "Drawback declaration row not found"
    box = m.group(1).replace("&nbsp;", " ")
    assert "[X] Yes" in box
    assert "[ ] No" in box
    assert "[X] No" not in box


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
    assert re.search(r"Assessable value", text)  # official column header verbatim
    assert re.search(r"Drawback", text)  # official declaration wording verbatim


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
    """A qty-9 document renders a different checksum than the qty-8 one.

    Since wave 1 the rendered quantity comes from field_values (the single
    source), so a quantity change must update field_values too.
    """
    qty8 = _complete_data()
    qty9 = qty8.model_copy(
        update={
            "quantity": 9,
            "field_values": {**qty8.field_values, "quantity_unit": 9},
        }
    )
    doc8 = render(qty8, "PBE_IV", out_path=tmp_path / "q8.pdf")
    doc9 = render(qty9, "PBE_IV", out_path=tmp_path / "q9.pdf")
    assert doc8.checksum != doc9.checksum
