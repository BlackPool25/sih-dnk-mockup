"""Tests for the todo-14 OFFICIAL PBE/CN22 filling rules.

``validate_document_rules`` (app/services/validate.py) enforces the portal's
own error taxonomy from pbe-iii-iv-fields.md §7 / SOP v1.3 — every violation
must surface the EXACT official rejection string, and every rule has a happy +
violation test here.  Also covers the SDR-driven CN22/CN23 auto-selection
(the 300-SDR threshold decides the label, never the user) and the DGFT/KYC
gates in the CLI.

Like the rest of the suite these hit the LIVE seeded DB (container up);
``documents`` rows created are cleaned up (immutable versioning).
"""

import re
import shutil
import subprocess

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, update

from app.db import SessionLocal
from app.models import Document, FillingRule
from app.services.cache import cache
from app.schemas.shipment import Shipment
from app.services.docs.__main__ import main as docs_cli_main
from app.services.docs.document import build_document_data
from app.services.docs.renderer import build_html, build_preview, render, sdr_info
from app.services.validate import (
    MSG_DESC_HS,
    MSG_DGFT_IEC_MISSING,
    MSG_FOB_INVOICE,
    MSG_GROSS_110_NET,
    MSG_ITCH_RESTRICTED,
    MSG_KYC_IEC_OR_GSTIN,
    MSG_SUB_PIECE_VALUE,
    MSG_SUB_PIECE_WEIGHT,
    validate_document_rules,
    validate_shipment,
)

IEC = "IN1234567890"
GSTIN = "29ABCDE1234F1Z5"

# 1 SDR = 10942 minor (₹109.42, itps-lane.md) ⇒ 300 SDR = ₹32,826.
SDR_THRESHOLD_MINOR = 300 * 10942


def _shipment(category: str = "embroidered-home-textiles", **kw) -> Shipment:
    return validate_shipment(
        Shipment(
            product_category=category,
            quantity=kw.get("quantity", 8),
            weight_grams=kw.get("weight_grams", 400),
            destination_country="US",
            confidence="high",
        )
    )


def _data(category: str = "embroidered-home-textiles", form: str = "PBE_IV", **kw):
    """A complete DocumentData (IEC+GSTIN set) with optional overrides.

    ``value_minor`` / ``consignee`` / ``iec`` / ``gstin`` go to
    ``build_document_data``; every other keyword is applied as a
    ``model_copy`` override so the filling-rule inputs (net_weight_g,
    fob_minor, unit_value_minor, piece_gross_g, category_name, …) can be
    violated directly.
    """
    build_kw = {
        key: kw.pop(key)
        for key in ("value_minor", "consignee", "iec", "gstin")
        if key in kw
    }
    build_kw.setdefault("iec", IEC)
    build_kw.setdefault("gstin", GSTIN)
    data = build_document_data(_shipment(category), form, **build_kw)
    return data.model_copy(update=kw)


def _doc_count(doc_type: str) -> int:
    with SessionLocal() as session:
        return session.scalar(
            select(func.count()).select_from(Document).where(Document.doc_type == doc_type)
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
        for row in rows:
            row.supersedes_doc_id = None
        session.flush()
        for row in rows:
            session.delete(row)
        session.commit()


# --- gross <= 110% of net ---------------------------------------------------


def test_gross_weight_rule_happy_path():
    # net defaults to gross (400 g) ⇒ 400 <= 440 — passes.
    assert validate_document_rules(_data()).errors == []


def test_gross_weight_exceeding_110_percent_of_net_rejects():
    r = validate_document_rules(_data(net_weight_g=300))  # 400 > 330
    assert MSG_GROSS_110_NET in r.errors


# --- wave 2: rules are read from the filling_rules DB table ------------------


def test_rules_db_driven_disable():
    """Disabling gross_net_110 in the DB disables the check — the rule chain
    is data, not hardcoded code."""
    try:
        with SessionLocal.begin() as session:
            session.execute(
                update(FillingRule)
                .where(FillingRule.rule_key == "gross_net_110")
                .values(enabled=False)
            )
        cache.delete("filling_rules:all")
        r = validate_document_rules(_data(net_weight_g=300))  # 400 > 330
        assert MSG_GROSS_110_NET not in r.errors
    finally:
        with SessionLocal.begin() as session:
            session.execute(
                update(FillingRule)
                .where(FillingRule.rule_key == "gross_net_110")
                .values(enabled=True)
            )
        cache.delete("filling_rules:all")


def test_rules_db_driven_params_and_messages():
    """The rejection message comes from the DB row, not a code constant."""
    with SessionLocal() as session:
        db_message = session.scalar(
            select(FillingRule.message).where(FillingRule.rule_key == "gross_net_110")
        )
    r = validate_document_rules(_data(net_weight_g=300))  # 400 > 330
    assert db_message in r.errors


# --- FOB <= invoice value ---------------------------------------------------


def test_fob_rule_happy_path():
    # FOB defaults to the declared cost value ⇒ FOB == invoice — passes.
    r = validate_document_rules(_data(value_minor=200000))
    assert MSG_FOB_INVOICE not in r.errors


def test_fob_exceeding_invoice_value_rejects():
    r = validate_document_rules(_data(value_minor=200000, fob_minor=500000))
    assert MSG_FOB_INVOICE in r.errors


# --- sum of piece values <= parcel value ------------------------------------


def test_sub_piece_values_rule_happy_path():
    # 8 pieces x 20000 = 160000 <= 200000 parcel value — passes.
    r = validate_document_rules(
        _data(value_minor=200000, unit_value_minor=20000)
    )
    assert MSG_SUB_PIECE_VALUE not in r.errors


def test_sub_piece_values_exceeding_parcel_value_rejects():
    # 8 x 30000 = 240000 > 200000 — the official rejection string verbatim.
    r = validate_document_rules(
        _data(value_minor=200000, unit_value_minor=30000)
    )
    assert MSG_SUB_PIECE_VALUE in r.errors


# --- sum of piece gross weights <= parcel weight ----------------------------


def test_sub_piece_weights_rule_happy_path():
    # 8 x 50 = 400 <= 400 parcel weight — passes.
    r = validate_document_rules(_data(piece_gross_g=50))
    assert MSG_SUB_PIECE_WEIGHT not in r.errors


def test_sub_piece_weights_exceeding_parcel_weight_rejects():
    # 8 x 60 = 480 > 400 — the official rejection string verbatim.
    r = validate_document_rules(_data(piece_gross_g=60))
    assert MSG_SUB_PIECE_WEIGHT in r.errors


# --- description <-> HS/CTH -------------------------------------------------


def test_description_hs_rule_happy_path():
    # DB-curated category name is consistent with its researched HS code.
    assert MSG_DESC_HS not in validate_document_rules(_data()).errors


def test_description_without_hs_word_overlap_rejects():
    # A category name with no word overlap to the HS description is rejected
    # with the exact official string.
    r = validate_document_rules(_data(category_name="Ceramic Tableware"))
    assert MSG_DESC_HS in r.errors


# --- ITCH restricted-policy warning (WARN, never a reject) ------------------


def test_itch_restricted_policy_warning_not_reject():
    # No seeded hs_codes row carries a restricted ITCH code, so the happy path
    # has no warning; a selected restricted code (5303 raw jute fibre —
    # jute-products §1) surfaces the official warning WITHOUT blocking.
    data = _data(category="jute-products", form="PBE_III")
    r = validate_document_rules(data)
    assert MSG_ITCH_RESTRICTED not in r.warnings
    assert r.errors == []

    r2 = validate_document_rules(
        data.model_copy(
            update={
                "hs_codes": [
                    {"hs6": "5303", "itc_hs_8": None, "description": "Raw jute fibre"}
                ]
            }
        )
    )
    assert MSG_ITCH_RESTRICTED in r2.warnings
    assert MSG_ITCH_RESTRICTED not in r2.errors


# --- DGFT / KYC gates -------------------------------------------------------


def test_kyc_gate_rejects_without_iec_or_gstin():
    # KYC Note-1: booking requires >= 1 of IEC/GSTIN — the KYC message wins.
    r = validate_document_rules(_data(iec=None, gstin=None))
    assert MSG_KYC_IEC_OR_GSTIN in r.errors
    assert MSG_DGFT_IEC_MISSING not in r.errors


def test_dgft_gate_rejects_when_iec_missing_but_gstin_present():
    # KYC passes (GSTIN present) but the DGFT/IEC registration is missing.
    r = validate_document_rules(_data(iec=None, gstin=GSTIN))
    assert MSG_DGFT_IEC_MISSING in r.errors
    assert MSG_KYC_IEC_OR_GSTIN not in r.errors


def test_kyc_and_dgft_gates_pass_with_iec():
    r = validate_document_rules(_data(iec=IEC))
    assert MSG_KYC_IEC_OR_GSTIN not in r.errors
    assert MSG_DGFT_IEC_MISSING not in r.errors


# --- render-level: rules block BEFORE WeasyPrint, no PDF, no row ------------


class _BoomWeasyPrint:
    """write_pdf raises — proves the renderer never reached WeasyPrint."""

    def __init__(self, *args, **kwargs):
        del args, kwargs

    def write_pdf(self, *args, **kwargs):
        del args, kwargs
        raise AssertionError("WeasyPrint was called for a rule-violating document")


def test_rules_gate_before_weasyprint_writes_nothing(tmp_path, monkeypatch, clean_documents):
    monkeypatch.setattr("app.services.docs.renderer.weasyprint.HTML", _BoomWeasyPrint)
    before = _doc_count("PBE_IV")
    out = tmp_path / "never.pdf"
    data = _data(net_weight_g=300)  # gross 400 > 330
    with pytest.raises(ValidationError) as excinfo:
        render(data, "PBE_IV", out_path=out)
    assert MSG_GROSS_110_NET in str(excinfo.value)
    assert not out.exists()
    assert _doc_count("PBE_IV") == before


# --- CLI: DGFT/KYC gates ----------------------------------------------------


def test_cli_rejects_without_iec_or_gstin(capsys):
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
                "--value-minor",
                "200000",
                "--consignee",
                "Jane Doe, 123 Main St",
            ]
        )
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert MSG_KYC_IEC_OR_GSTIN in err


def test_cli_renders_with_iec_and_gstin(tmp_path, clean_documents):
    out = tmp_path / "with_kyc.pdf"
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
            IEC,
            "--gstin",
            GSTIN,
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


# --- SDR / CN22-CN23 auto-selection (never user-picked) ---------------------


def test_sdr_info_low_value_selects_cn22():
    sdr = sdr_info(2000)  # Rs 20 parcel
    assert sdr["cn_form"] == "CN22"
    assert sdr["max_sdr"] == 300
    assert sdr["threshold_minor"] == SDR_THRESHOLD_MINOR
    assert sdr["sdr_minor"] == 18  # 2000 * 100 / 10942 = 18.28 -> 18 (0.18 SDR)


def test_sdr_info_high_value_selects_cn23():
    sdr = sdr_info(4_000_000)  # Rs 40,000 > 300 SDR (~Rs 32,826)
    assert sdr["cn_form"] == "CN23"
    assert sdr["sdr_minor"] == 36556  # 4_000_000 * 100 / 10942


def test_cn22_renders_for_low_value_parcel(tmp_path, clean_documents):
    data = _data(form="CN22", value_minor=2000)
    out = tmp_path / "cn22.pdf"
    doc = render(data, "CN22", out_path=out)
    assert doc.doc_type == "CN22"
    assert out.exists()
    html = build_html(data, "CN22")
    assert "Auto-computed SDR value: 0.18 SDR" in html
    assert "auto-selected label: <strong>CN22</strong>" in html


def test_cn23_auto_selects_for_high_value_parcel_even_when_cn22_requested(
    tmp_path, clean_documents
):
    # Requesting CN22 for a >300-SDR parcel MUST auto-select CN23 — the label
    # is derived from the value, never user-picked (document-stack.md §10).
    data = _data(form="CN22", value_minor=4_000_000)
    out = tmp_path / "derived_cn23.pdf"
    doc = render(data, "CN22", out_path=out)
    assert doc.doc_type == "CN23"
    assert out.exists()


def test_cn23_renders_for_high_value_parcel(tmp_path, clean_documents):
    data = _data(form="CN23", value_minor=4_000_000)
    out = tmp_path / "cn23.pdf"
    doc = render(data, "CN23", out_path=out)
    assert doc.doc_type == "CN23"
    assert out.exists()
    html = build_html(data, "CN23")
    assert "Auto-computed SDR value: 365.56 SDR" in html
    assert "auto-selected label: <strong>CN23</strong>" in html


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext missing")
def test_cn22_pdf_shows_sdr_and_choice(tmp_path, clean_documents):
    out = tmp_path / "cn22.pdf"
    render(_data(form="CN22", value_minor=2000), "CN22", out_path=out)
    text = subprocess.run(
        ["pdftotext", str(out), "-"], check=True, capture_output=True, text=True
    ).stdout
    assert re.search(r"0\.18 SDR", text)
    assert re.search(r"CN22", text)


# --- SDR enforcement gate: the label is derived, never user-picked ----------


def _last_document_row():
    with SessionLocal() as session:
        return session.scalar(select(Document).order_by(Document.id.desc()).limit(1))


def test_cn22_high_value_auto_switches_to_cn23(tmp_path, capsys, clean_documents):
    """--form CN22 with a >300-SDR value MUST render CN23, record CN23 in the
    documents row, and say so in the CLI output."""
    out = tmp_path / "highval.pdf"
    rc = docs_cli_main(
        [
            "render", "--category", "embroidered-home-textiles", "--qty", "8",
            "--weight-g", "400", "--country", "US", "--form", "CN22",
            "--iec", IEC, "--gstin", GSTIN, "--value-minor", "5000000",
            "--out", str(out),
        ]
    )
    assert rc == 0
    printed = capsys.readouterr().out
    assert "using CN23 instead of CN22" in printed
    assert out.exists()
    row = _last_document_row()
    assert row.doc_type == "CN23"
    assert row.structured_json["form_type"] == "CN23"


def test_cn23_low_value_auto_switches_to_cn22(tmp_path, capsys, clean_documents):
    """--form CN23 with a <=300-SDR value MUST render CN22, record CN22, and
    say so in the CLI output."""
    out = tmp_path / "lowval.pdf"
    rc = docs_cli_main(
        [
            "render", "--category", "embroidered-home-textiles", "--qty", "8",
            "--weight-g", "400", "--country", "US", "--form", "CN23",
            "--iec", IEC, "--gstin", GSTIN, "--value-minor", "2000",
            "--out", str(out),
        ]
    )
    assert rc == 0
    printed = capsys.readouterr().out
    assert "using CN22 instead of CN23" in printed
    assert out.exists()
    row = _last_document_row()
    assert row.doc_type == "CN22"
    assert row.structured_json["form_type"] == "CN22"


def test_cn22_low_value_stays_cn22_without_switch_note(tmp_path, capsys, clean_documents):
    """A <=300-SDR parcel requested as CN22 stays CN22 — no switch note."""
    out = tmp_path / "staycn22.pdf"
    rc = docs_cli_main(
        [
            "render", "--category", "embroidered-home-textiles", "--qty", "8",
            "--weight-g", "400", "--country", "US", "--form", "CN22",
            "--iec", IEC, "--gstin", GSTIN, "--value-minor", "2000",
            "--out", str(out),
        ]
    )
    assert rc == 0
    assert "instead of" not in capsys.readouterr().out
    assert _last_document_row().doc_type == "CN22"


def test_pbe_form_unaffected_by_sdr_gate(tmp_path, capsys, clean_documents):
    """The SDR switch only applies to CN22/CN23 — a PBE render with any value
    keeps its doc_type and prints no switch note."""
    out = tmp_path / "pbe.pdf"
    rc = docs_cli_main(
        [
            "render", "--category", "embroidered-home-textiles", "--qty", "8",
            "--weight-g", "400", "--country", "US", "--form", "PBE_IV",
            "--iec", IEC, "--gstin", GSTIN, "--value-minor", "5000000",
            "--consignee", "Jane Doe, 123 Main St",
            "--out", str(out),
        ]
    )
    assert rc == 0
    assert "instead of" not in capsys.readouterr().out
    assert _last_document_row().doc_type == "PBE_IV"


def test_build_html_enforces_switch_consistency():
    """Direct build_html calls also enforce the gate: the rendered form type
    matches the derived label — never a 'CN22 form showing choice CN23'."""
    data = _data(form="CN22", value_minor=5_000_000)  # >300 SDR
    html = build_html(data, "CN22")
    assert "CN23 — this detailed customs declaration" in html  # CN23 template
    assert "auto-selected label: <strong>CN23</strong>" in html
    assert "CN22 — this customs declaration" not in html

    low = _data(form="CN23", value_minor=2000)  # <=300 SDR
    html_low = build_html(low, "CN23")
    assert "CN22 — this customs declaration" in html_low
    assert "auto-selected label: <strong>CN22</strong>" in html_low


def test_preview_note_surfaces_the_switch():
    pv = build_preview(_data(form="CN22", value_minor=5_000_000))
    assert "using CN23 instead of CN22" in pv
