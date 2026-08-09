"""Deterministic document renderer (todo 11).

Pipeline, in order:

1. GATE — ``DocumentData.model_validate`` + ``missing_required(...) == []``.
   Any required ``pbe_field_schemas`` field without a source value raises a
   pydantic ``ValidationError`` listing the missing fields BEFORE WeasyPrint
   is ever touched.  This is the only validity gate — the LLM never validates.
2. HTML — Jinja2 templates under ``templates/``; PBE forms iterate the
   ``pbe_field_schemas`` sections/fields from the DB (NOT hardcoded); values
   are filled where they map onto the DocumentData, else "—".
3. PDF — WeasyPrint writes to ``docs-out/`` (git-ignored).
4. IMMUTABLE VERSIONING — sha256 checksum; ``version = max(version)+1`` with
   ``supersedes_doc_id = previous max id``; a NEW row is INSERTed per render.
   Rows are never updated or overwritten.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import NoReturn

import weasyprint
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Document, PbeFieldSchema
from app.services.db_tools import get_config_flag
from app.services.docs.document import (
    FORM_TYPES,
    DocumentData,
    to_shipment,
)
from app.services.validate import missing_required

DOCS_OUT = Path("docs-out")  # git-ignored (see .gitignore)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_JINJA = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)

# Form type -> template file (exactly the six files in templates/).
_TEMPLATE_FILE: dict[str, str] = {
    "PBE_III": "pbe_iii.html",
    "PBE_IV": "pbe_iv.html",
    "CN22": "cn22.html",
    "CN23": "cn23.html",
    "INVOICE": "invoice.html",
    "PACKING_LIST": "packing_list.html",
}

_DOC_TITLES: dict[str, str] = {
    "PBE_III": "Bill of Export — PBE-III",
    "PBE_IV": "Bill of Export — PBE-IV",
    "CN22": "Customs Declaration CN22",
    "CN23": "Customs Declaration CN23",
    "INVOICE": "Commercial Invoice",
    "PACKING_LIST": "Packing List",
}

# Shared page chrome for every template (fontconfig-resolved fonts — NOT
# bundled; Devanagari/Kannada faces are declared so the preview/UI scripts
# would render, but the English form content never needs them).
_CSS = """
@page { size: A4; margin: 16mm 14mm; }
body {
  font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Kannada',
               sans-serif;
  font-size: 10pt; color: #111; line-height: 1.45;
}
h1 { font-size: 14pt; margin: 0 0 2pt; }
.subtitle { font-size: 9pt; color: #555; margin: 0 0 12pt; }
h2 {
  font-size: 11pt; margin: 14pt 0 6pt; padding: 3pt 6pt;
  background: #eef1f5; border-left: 3pt solid #33475b;
}
table { width: 100%; border-collapse: collapse; margin-bottom: 4pt; }
th, td {
  border: 0.5pt solid #888; padding: 4pt 6pt; text-align: left;
  vertical-align: top;
}
th { width: 38%; background: #f7f8fa; font-weight: 600; }
td { width: 62%; }
.missing { color: #777; font-style: italic; }
.footer {
  margin-top: 14pt; font-size: 8.5pt; color: #666;
  border-top: 0.5pt solid #aaa; padding-top: 4pt;
}
"""


def _money(minor: int | None) -> str:
    """Render an INR minor-unit amount as rupees — "—" when absent."""
    if minor is None:
        return "—"
    return f"₹{minor / 100:,.2f}"


def _primary_hs(data: DocumentData) -> dict | None:
    """The first HS row (lookup_hs_codes orders by hs6, deterministically)."""
    return data.hs_codes[0] if data.hs_codes else None


def _field_value(data: DocumentData, field_key: str) -> str:
    """Map a pbe_field_schemas field_key onto the DocumentData — else "—".

    Every mapped value traces back to a validated Shipment key, a db_tools
    lookup, or a CLI order field.  Fields outside the contract (iec,
    invoice_no_date, decl.*, ecomm_*, …) have no data source and are rendered
    as "—" — the form is honest about what it does not know.
    """
    if field_key == "consignee_details":
        parts = [data.consignee] if data.consignee else []
        parts.append(data.destination_country)
        return " / ".join(parts)
    if field_key == "product_description":
        return data.category_name
    if field_key == "cth":
        hs = _primary_hs(data)
        return hs["hs6"][:4] if hs else "—"
    if field_key == "ritc_itc_hs":
        hs = _primary_hs(data)
        return (hs["itc_hs_8"] or hs["hs6"]) if hs else "—"
    if field_key == "quantity_unit":
        return f"{data.quantity} Nos"
    if field_key in ("gross_weight", "net_weight"):
        return f"{data.weight_grams} g"
    if field_key == "assessable_value":
        return _money(data.value_minor)
    return "—"


def _summary_rows(data: DocumentData) -> list[dict]:
    """Rows for the CN22/CN23/INVOICE/PACKING_LIST forms (no PBE schema rows).

    ``value_minor`` / ``consignee`` are the optional CLI fields — rendered as
    "—" when omitted (user-requirement: optional details are only filled when
    the user supplies them).
    """
    hs = _primary_hs(data)
    desc = hs["description"] if hs else "—"
    hs_list = ", ".join(h["hs6"] for h in data.hs_codes[:5]) or "—"
    common = [
        {"label": "Description of contents", "value": desc},
        {"label": "Quantity", "value": f"{data.quantity} Nos"},
        {"label": "Weight (g)", "value": f"{data.weight_grams} g"},
    ]
    if data.form_type == "CN22":
        return common + [
            {"label": "Destination country", "value": data.destination_country}
        ]
    rows: list[dict] = [
        {"label": "Consignee", "value": data.consignee or "—"},
        {"label": "Destination country", "value": data.destination_country},
        *common,
        {"label": "HS code(s)", "value": hs_list},
        {"label": "Declared value", "value": _money(data.value_minor)},
    ]
    if data.form_type == "INVOICE":
        rows += [
            {"label": "Freight (ITPS)", "value": _money(data.lane["cost_minor"])},
            {"label": "Landed cost", "value": _money(data.landed_cost_minor)},
        ]
    return rows


def _load_form_fields(doc_type: str) -> list[dict]:
    """pbe_field_schemas rows for a form type, in id order (drives the form)."""
    with SessionLocal() as session:
        rows = session.scalars(
            select(PbeFieldSchema)
            .where(PbeFieldSchema.form_type == doc_type)
            .order_by(PbeFieldSchema.id)
        ).all()
    return [
        {
            "field_key": row.field_key,
            "section": row.section,
            "label": row.label,
            "required": row.required,
        }
        for row in rows
    ]


def _sections(data: DocumentData, fields: list[dict]) -> list[dict]:
    """Group pbe_field_schemas fields by section (order preserved)."""
    sections: list[dict] = []
    for field in fields:
        name = field["section"] or "General"
        if not sections or sections[-1]["name"] != name:
            sections.append({"name": name, "rows": []})
        value = _field_value(data, field["field_key"])
        sections[-1]["rows"].append(
            {
                "label": field["label"],
                "value": value,
                "required": field["required"],
                "missing": field["required"] and value == "—",
            }
        )
    return sections


def _raise_missing(missing: list[str], fields: list[dict]) -> NoReturn:
    """pydantic ValidationError listing the missing pbe_field_schemas fields."""
    labels = {f["field_key"]: f["label"] for f in fields}
    line_errors = [
        {
            "type": "value_error",
            "loc": (key,),
            "msg": f"required PBE field {key!r} ({labels.get(key, key)}) "
            f"has no value in the document data",
            "input": None,
            "ctx": {"error": ValueError(f"missing required field {key!r}")},
        }
        for key in missing
    ]
    raise ValidationError.from_exception_data("DocumentData", line_errors)


def _gate_completeness(data: DocumentData, doc_type: str) -> None:
    """Deterministic completeness gate — the ONLY validity check besides the
    Pydantic shape check.  Raises before WeasyPrint is ever called."""
    missing = missing_required(to_shipment(data), doc_type)
    if missing:
        _raise_missing(missing, _load_form_fields(doc_type))


def build_html(document_data: DocumentData, doc_type: str) -> str:
    """Render the form HTML via Jinja2 — English content only.

    PBE forms iterate the pbe_field_schemas sections/fields from the DB; the
    simple forms (CN22/CN23/invoice/packing list) use summary rows.  The
    context carries NO Hindi/Kannada text — bilingual labels are preview/UI
    only (see ``build_preview``).
    """
    data = DocumentData.model_validate(document_data)
    if doc_type not in _TEMPLATE_FILE:
        raise ValueError(
            f"unknown doc_type {doc_type!r} — expected one of {list(FORM_TYPES)}"
        )
    if data.form_type != doc_type:
        raise ValueError(
            f"doc_type {doc_type!r} does not match DocumentData.form_type "
            f"{data.form_type!r}"
        )
    ctx: dict = {
        "doc_title": _DOC_TITLES[doc_type],
        "css": _CSS,
        "rows": _summary_rows(data),
        "sections": _sections(data, _load_form_fields(doc_type)),
    }
    return _JINJA.get_template(_TEMPLATE_FILE[doc_type]).render(**ctx)


def build_preview(document_data: DocumentData) -> str:
    """Readable form summary for the confirmation UI.

    Shows every pbe_field_schemas section/field + its value (required fields
    marked) plus the hi/kn confirm labels from ``config_flags``
    (``labels.confirm.hi`` = कृपया पुष्टि करें, ``labels.confirm.kn`` =
    ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ).  This is the ONLY place the bilingual labels
    appear — never in the rendered form.
    """
    data = DocumentData.model_validate(document_data)
    lines = [
        f"Document preview — {_DOC_TITLES[data.form_type]}",
        "=" * 52,
        f"Category      : {data.category_name} ({data.category_slug})",
        f"Quantity      : {data.quantity}",
        f"Weight        : {data.weight_grams} g",
        f"Destination   : {data.destination_country}",
        (
            f"Freight (ITPS): {_money(data.lane['cost_minor'])}"
            f" (cost_minor {data.lane['cost_minor']})"
        ),
        f"HS codes      : {', '.join(h['hs6'] for h in data.hs_codes[:5]) or '—'}",
        f"Duty rows     : {len(data.duties)}",
        f"Consignee     : {data.consignee or '—'}",
        f"Declared value: {_money(data.value_minor)}",
        "",
    ]
    for section in _sections(data, _load_form_fields(data.form_type)):
        lines.append(f"[{section['name']}]")
        for row in section["rows"]:
            mark = " *" if row["required"] else ""
            lines.append(f"  {row['label']:<34} {row['value']}{mark}")
        lines.append("")
    hi = get_config_flag("labels.confirm.hi")["flag_value"]
    kn = get_config_flag("labels.confirm.kn")["flag_value"]
    lines += [
        "Confirm (हिन्दी): " + hi,
        "Confirm (ಕನ್ನಡ): " + kn,
    ]
    return "\n".join(lines)


def _checksum(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()


def _next_version(doc_type: str) -> tuple[int, int | None]:
    """Immutable versioning: max(version)+1, superseding the previous max id.

    A new row is ALWAYS inserted — existing rows are never updated.
    """
    with SessionLocal() as session:
        prev = session.scalar(
            select(Document)
            .where(Document.doc_type == doc_type)
            .order_by(Document.version.desc(), Document.id.desc())
            .limit(1)
        )
        version = prev.version + 1 if prev is not None else 1
        supersedes = prev.id if prev is not None else None
    return version, supersedes


def render(
    document_data: DocumentData,
    doc_type: str,
    out_path: str | Path | None = None,
) -> Document:
    """Render a document: gate -> Jinja2 -> WeasyPrint -> sha256 -> new row.

    Args:
        document_data: DocumentData (or dict shaped like it — model_validate).
        doc_type: one of FORM_TYPES.
        out_path: PDF destination (default ``docs-out/{doc_type}-v{version}.pdf``).

    Returns:
        The persisted ``Document`` row (version 1, 2, … — never overwritten).

    Raises:
        ValueError: unknown ``doc_type`` or form-type mismatch.
        ValidationError: ``DocumentData`` shape invalid, or required
            pbe_field_schemas fields missing (raised BEFORE WeasyPrint).
    """
    data = DocumentData.model_validate(document_data)
    if doc_type not in _TEMPLATE_FILE:
        raise ValueError(
            f"unknown doc_type {doc_type!r} — expected one of {list(FORM_TYPES)}"
        )
    if data.form_type != doc_type:
        raise ValueError(
            f"doc_type {doc_type!r} does not match DocumentData.form_type "
            f"{data.form_type!r}"
        )
    _gate_completeness(data, doc_type)

    html = build_html(data, doc_type)
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    checksum = _checksum(pdf_bytes)
    version, supersedes = _next_version(doc_type)
    path = (
        Path(out_path)
        if out_path is not None
        else DOCS_OUT / f"{doc_type}-v{version}.pdf"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf_bytes)

    with SessionLocal() as session:
        row = Document(
            doc_type=doc_type,
            version=version,
            checksum=checksum,
            structured_json=data.model_dump(mode="json"),
            file_path=str(path),
            supersedes_doc_id=supersedes,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


__all__ = ["build_html", "build_preview", "render"]
