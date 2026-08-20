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
import sys
from pathlib import Path
from typing import NoReturn

import weasyprint
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Document, Order, PbeFieldSchema
from app.schemas.shipment import Shipment
from app.services.db_tools import get_config_flag
from app.services.docs.document import FORM_TYPES, DocumentData, build_document_data
from app.services.validate import missing_required, validate_document_rules

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

# Form type -> line-item template file (multi-product orders).
_LINE_TEMPLATE_FILE: dict[str, str] = {
    "INVOICE": "invoice_lines.html",
    "PACKING_LIST": "invoice_lines.html",
}

_DOC_TITLES: dict[str, str] = {
    "PBE_III": "Postal Bill of Export - III",
    "PBE_IV": "Postal Bill of Export - IV",
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


def _summary_rows(data: DocumentData) -> list[dict]:
    """Rows for the CN22/CN23/INVOICE/PACKING_LIST forms (no PBE schema rows).

    Includes Exporter/Seller details from profile alongside Consignee and shipment specs.
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
        return common + [{"label": "Destination country", "value": data.destination_country}]

    sender_display = data.sender.name_address or data.field_values.get("exporter_name") or "—"
    if isinstance(sender_display, str) and "\n" in sender_display:
        sender_display = sender_display.replace("\n", ", ")

    rows: list[dict] = [
        {"label": "Exporter / Seller", "value": sender_display},
        {"label": "Exporter IEC", "value": data.iec or data.sender.sender_ref or "—"},
        {"label": "Consignee", "value": data.consignee or "—"},
        {"label": "Destination country", "value": data.destination_country},
        *common,
        {"label": "HS code(s)", "value": hs_list},
        {"label": "Declared value", "value": _money(data.value_minor)},
    ]
    if data.form_type == "INVOICE":
        lane_name = data.lane.get("lane") if isinstance(data.lane, dict) else "ITPS"
        if lane_name not in ("ITPS", "EMS"):
            lane_name = "ITPS"
        rows += [
            {"label": f"Freight ({lane_name})", "value": _money(data.lane["cost_minor"])},
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
        value = data.resolve_value(field["field_key"])
        sections[-1]["rows"].append(
            {
                "field_key": field["field_key"],
                "label": field["label"],
                "value": value,
                "required": field["required"],
                "missing": field["required"] and value == "—",
            }
        )
    return sections


def _by_key(sections: list[dict]) -> dict[str, dict]:
    """Flat field_key -> row lookup for the columnar PBE templates."""
    by_key: dict[str, dict] = {}
    for section in sections:
        for row in section["rows"]:
            by_key[row["field_key"]] = row
    return by_key


def _sdr_value(sdr_minor: int | None) -> str:
    """Render an SDR figure (2-decimals) — "—" when no value was declared."""
    if sdr_minor is None:
        return "—"
    return f"{sdr_minor / 100:,.2f} SDR"


def sdr_info(value_minor: int | None) -> dict:
    """SDR figure + CN22/CN23 auto-selection (todo 14, document-stack.md §10).

    The 300-SDR threshold ONLY decides the label — the DNK portal auto-computes
    the SDR value and the exporter never enters it (pbe-iii-iv-fields.md §5).
    CN22 when ``value_minor <= max_sdr * fx``, else CN23.  ``fx`` is the seeded
    estimate ``sdr.fx_minor_per_sdr`` (1 SDR ≈ ₹109.42, itps-lane.md §6); with
    no declared value the CN22 default applies (low-value assumption).
    """
    sdr_fx_minor = int(get_config_flag("sdr.fx_minor_per_sdr")["flag_value"])
    max_sdr = int(get_config_flag("cn22.sdr_max")["flag_value"])
    threshold_minor = max_sdr * sdr_fx_minor
    if value_minor is None:
        return {
            "sdr_minor": None,
            "fx_minor_per_sdr": sdr_fx_minor,
            "max_sdr": max_sdr,
            "threshold_minor": threshold_minor,
            "cn_form": "CN22",
        }
    return {
        "sdr_minor": round(value_minor * 100 / sdr_fx_minor),  # 2-dec SDR minor
        "fx_minor_per_sdr": sdr_fx_minor,
        "max_sdr": max_sdr,
        "threshold_minor": threshold_minor,
        "cn_form": "CN22" if value_minor <= threshold_minor else "CN23",
    }


def _cn_switch_note(requested: str, resolved: str, value_minor: int) -> str:
    """Human note for an SDR-driven CN22/CN23 auto-switch (never user-picked)."""
    relation = "exceeds 300 SDR" if resolved == "CN23" else "is within 300 SDR"
    return f"value {_money(value_minor)} {relation} — using {resolved} instead of {requested}"


def _resolve_cn_label(data: DocumentData, doc_type: str) -> tuple[str, DocumentData]:
    """SDR enforcement gate: the CN22/CN23 label is derived from the declared
    value (300-SDR threshold, document-stack.md §10) — NEVER user-picked.

    Returns the ``(resolved doc_type, resolved DocumentData)``.  When the
    derived label differs from the requested one, the form AND its
    ``data.form_type`` are switched so the rendered ``sdr_choice`` always
    equals the rendered form.  With no declared value the CN22 default applies
    (low-value assumption, documented) — no switch.
    """
    if doc_type in ("CN22", "CN23") and data.value_minor is not None:
        derived = sdr_info(data.value_minor)["cn_form"]
        if derived != doc_type:
            return derived, data.model_copy(update={"form_type": derived})
    return doc_type, data


def _cn_context(data: DocumentData) -> dict:
    """UPU CN22/CN23 block data — sender/consignee/contents + SDR note.

    The sender block comes from ``data.sender`` (SellerBlock — the seller
    supplies it via the CLI later); each field renders "—" when unset (the
    exporter fills them at the counter).  The SDR note follows
    document-stack.md §10: CN22 for items up to 300 SDR, CN23 for items over
    300 SDR; the DNK portal auto-computes the SDR value.
    """
    hs = _primary_hs(data)
    note = (
        "CN23 — this detailed customs declaration is required when the value "
        "of the contents exceeds 300 SDR (Special Drawing Rights) and is "
        "usually accompanied by the commercial invoice. The SDR value is "
        "computed automatically by the DNK portal (India Post) — the exporter "
        "need not enter it."
        if data.form_type == "CN23"
        else "CN22 — this customs declaration is used for items with a value "
        "of up to 300 SDR (Special Drawing Rights). If the value exceeds "
        "300 SDR, the CN23 form must be used instead. The SDR value is "
        "computed automatically by the DNK portal (India Post) — the exporter "
        "need not enter it."
    )
    sdr = sdr_info(data.value_minor)
    return {
        "sender": data.sender.name_address or "—",
        "sender_ref": data.sender.sender_ref or "—",
        "consignee": data.consignee or "—",
        "destination": data.destination_country,
        "description": hs["description"] if hs else "—",
        "hs": hs["hs6"] if hs else "—",
        "qty": f"{data.quantity} Nos",
        "weight": f"{data.weight_grams} g",
        "value": _money(data.value_minor),
        "non_delivery": data.sender.non_delivery or "—",
        "num_invoices": data.sender.num_invoices or "—",
        "sdr_value": _sdr_value(sdr["sdr_minor"]),
        "sdr_choice": sdr["cn_form"],
        "sdr_threshold": f"{sdr['max_sdr']} SDR",
        "sdr_fx": f"1 SDR = ₹{sdr['fx_minor_per_sdr'] / 100:.2f}",
        "sdr_note": note,
    }


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


def _raise_rules_error(errors: list[str]) -> NoReturn:
    """pydantic ValidationError listing the official filling-rule rejections.

    Carries the portal's exact rejection strings (pbe-iii-iv-fields.md §7) —
    never paraphrased.
    """
    line_errors = [
        {
            "type": "value_error",
            "loc": ("rules",),
            "msg": err,
            "input": None,
            "ctx": {"error": ValueError(err)},
        }
        for err in errors
    ]
    raise ValidationError.from_exception_data("DocumentData", line_errors)


def _gate_completeness(data: DocumentData, doc_type: str) -> None:
    """Deterministic completeness gate — the ONLY validity check besides the
    Pydantic shape check.  Raises before WeasyPrint is ever called."""
    missing = missing_required(data, doc_type)
    if missing:
        _raise_missing(missing, _load_form_fields(doc_type))


def build_html(
    document_data: DocumentData,
    doc_type: str,
    *,
    line_docs: list[dict] | None = None,
) -> str:
    """Render the form HTML via Jinja2 — English content only.

    PBE forms iterate the pbe_field_schemas sections/fields from the DB; the
    simple forms (CN22/CN23/invoice/packing list) use summary rows.  When
    ``line_docs`` is provided for INVOICE/PACKING_LIST, the line-item template
    is used instead.  The context carries NO Hindi/Kannada text — bilingual
    labels are preview/UI only (see ``build_preview``).
    """
    data = DocumentData.model_validate(document_data)
    if doc_type not in _TEMPLATE_FILE:
        raise ValueError(f"unknown doc_type {doc_type!r} — expected one of {list(FORM_TYPES)}")
    if data.form_type != doc_type:
        raise ValueError(
            f"doc_type {doc_type!r} does not match DocumentData.form_type {data.form_type!r}"
        )
    # SDR enforcement gate (todo-14 fix): the CN22/CN23 label is derived from
    # the declared value, never user-picked — a CN22 request for a >300-SDR
    # parcel must render the CN23 form (and vice versa), so the form's
    # sdr_choice always equals the rendered form type.
    doc_type, data = _resolve_cn_label(data, doc_type)
    sections = _sections(data, _load_form_fields(doc_type))
    ctx: dict = {
        "doc_title": _DOC_TITLES[doc_type],
        "css": _CSS,
        "rows": _summary_rows(data),
        "sections": sections,
        "by_key": _by_key(sections),
        "cn": _cn_context(data) if doc_type in ("CN22", "CN23") else {},
    }
    if line_docs is not None and doc_type in _LINE_TEMPLATE_FILE:
        ctx["line_docs"] = line_docs
        return _JINJA.get_template(_LINE_TEMPLATE_FILE[doc_type]).render(**ctx)
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
            f"Freight ({data.lane.get('lane', 'ITPS') if isinstance(data.lane, dict) else 'ITPS'}): {_money(data.lane['cost_minor'])}"
            f" (cost_minor {data.lane['cost_minor']})"
        ),
        f"HS codes      : {', '.join(h['hs6'] for h in data.hs_codes[:5]) or '—'}",
        f"Duty rows     : {len(data.duties)}",
        f"Consignee     : {data.consignee or '—'}",
        f"Declared value: {_money(data.value_minor)}",
        "",
    ]
    if data.form_type in ("CN22", "CN23"):
        sdr = sdr_info(data.value_minor)
        sdr_lines = [
            (
                f"SDR value     : {_sdr_value(sdr['sdr_minor'])} → auto-selects "
                f"{sdr['cn_form']} (threshold {sdr['max_sdr']} SDR; "
                f"1 SDR = ₹{sdr['fx_minor_per_sdr'] / 100:.2f})"
            ),
        ]
        if data.value_minor is not None and sdr["cn_form"] != data.form_type:
            sdr_lines.append(
                "NOTE: " + _cn_switch_note(data.form_type, sdr["cn_form"], data.value_minor)
            )
        lines[-1:-1] = sdr_lines
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


def _order_id_kwargs(order: Order | None) -> dict[str, object]:
    """order_id kwargs for a new Document row — only when the column exists.

    W2-T5 adds ``documents.order_id`` via migration; the Document model file
    is deliberately not edited here, so rows written pre-migration must not
    reference the column.  ``getattr`` on the mapped class resolves to the
    InstrumentedAttribute once the model declares it, None before — the
    guard works both ways.
    """
    if order is None or getattr(Document, "order_id", None) is None:
        return {}
    return {"order_id": order.id}


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


def render_line_items(
    order: Order,
    doc_type: str,
    out_dir: str | Path | None = None,
) -> list[Document]:
    """Per-line document generation for multi-product orders.

    For invoice + packing_list: build one DocumentData per line item, collect
    per-line summaries into ``line_docs``, render a single combined HTML with
    the line-item template, produce one PDF with all line rows, and insert one
    Document row per line item.

    For PBE_III/PBE_IV/CN22/CN23: aggregate all line items into a single
    DocumentData (first line item's category for the HS lookup, sums for
    quantity/weight), render once with the standard template, and insert one
    Document row.

    Returns:
        list of Document rows — one per line item for INVOICE/PACKING_LIST,
        one for PBE/CN forms.
    """
    if doc_type not in _TEMPLATE_FILE:
        raise ValueError(f"unknown doc_type {doc_type!r} — expected one of {list(FORM_TYPES)}")
    if not order.line_items:
        raise ValueError("order has no line_items")
    destination = order.destination_country or "US"

    if doc_type in ("INVOICE", "PACKING_LIST"):
        # ── per-line build ──
        line_docs: list[dict] = []
        documents: list[Document] = []
        total_qty = 0
        total_weight = 0
        for idx, li in enumerate(order.line_items, start=1):
            cat = li.category_slug or "embroidered-home-textiles"
            qty = li.quantity or 1
            wgt = li.weight_g or 100
            total_qty += qty
            total_weight += wgt
            shipment = Shipment(
                product_category=cat,
                quantity=qty,
                weight_grams=wgt,
                destination_country=destination,
                confidence="high",
            )
            data = build_document_data(
                shipment,
                doc_type,
                consignee=order.consignee,
                value_minor=li.value_minor or order.value_minor,
                iec=order.iec,
                gstin=order.gstin,
                net_weight_g=order.net_weight_g,
            )
            hs = data.hs_codes[0] if data.hs_codes else None
            line_docs.append(
                {
                    "si_no": str(idx),
                    "description": hs["description"] if hs else (li.category_slug or "—"),
                    "quantity": f"{qty} Nos",
                    "weight_grams": f"{wgt} g",
                    "hs_code": li.hs_code or (hs["hs6"] if hs else "—"),
                    "value": _money(li.value_minor or order.value_minor),
                }
            )

        # ── overall DocumentData for the summary rows ──
        first_li = order.line_items[0]
        total_shipment = Shipment(
            product_category=first_li.category_slug or "embroidered-home-textiles",
            quantity=total_qty,
            weight_grams=total_weight,
            destination_country=destination,
            confidence="high",
        )
        total_data = build_document_data(
            total_shipment,
            doc_type,
            consignee=order.consignee,
            value_minor=order.value_minor,
            iec=order.iec,
            gstin=order.gstin,
            net_weight_g=order.net_weight_g,
        )

        # Gates
        rules = validate_document_rules(total_data)
        for warning in rules.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        if rules.errors:
            _raise_rules_error(rules.errors)
        _gate_completeness(total_data, doc_type)
        resolved_doc_type, total_data = _resolve_cn_label(total_data, doc_type)

        html = build_html(total_data, resolved_doc_type, line_docs=line_docs)
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        checksum = _checksum(pdf_bytes)
        version, supersedes = _next_version(resolved_doc_type)
        out_dir_path = Path(out_dir) if out_dir else DOCS_OUT
        path = out_dir_path / f"{resolved_doc_type}-v{version}.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pdf_bytes)

        # One Document row per line item
        with SessionLocal() as session:
            session.expire_on_commit = False
            for idx, li in enumerate(order.line_items, start=1):
                row = Document(
                    doc_type=resolved_doc_type,
                    version=version,
                    checksum=checksum,
                    structured_json=total_data.model_dump(mode="json"),
                    file_path=str(path),
                    supersedes_doc_id=supersedes,
                    **_order_id_kwargs(order),
                )
                session.add(row)
                documents.append(row)
            session.commit()
        return documents

    # ── PBE_III / PBE_IV / CN22 / CN23: aggregate all lines into one DocumentData ──
    first_li = order.line_items[0]
    cat = first_li.category_slug or "embroidered-home-textiles"
    total_qty = sum(li.quantity or 1 for li in order.line_items)
    total_weight = sum(li.weight_g or 100 for li in order.line_items)
    total_value = sum((li.value_minor or order.value_minor or 0) for li in order.line_items)

    shipment = Shipment(
        product_category=cat,
        quantity=total_qty,
        weight_grams=total_weight,
        destination_country=destination,
        confidence="high",
    )
    data = build_document_data(
        shipment,
        doc_type,
        consignee=order.consignee,
        value_minor=total_value if total_value > 0 else order.value_minor,
        iec=order.iec,
        gstin=order.gstin,
        net_weight_g=order.net_weight_g,
    )

    rules = validate_document_rules(data)
    for warning in rules.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if rules.errors:
        _raise_rules_error(rules.errors)
    _gate_completeness(data, doc_type)
    resolved_doc_type, data = _resolve_cn_label(data, doc_type)
    if resolved_doc_type != doc_type:
        print(_cn_switch_note(doc_type, resolved_doc_type, data.value_minor))
        doc_type = resolved_doc_type

    html = build_html(data, doc_type)
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    checksum = _checksum(pdf_bytes)
    version, supersedes = _next_version(doc_type)
    path = (
        Path(out_dir) / f"{doc_type}-v{version}.pdf"
        if out_dir
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
            **_order_id_kwargs(order),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
    return [row]


def render(
    document_data: DocumentData,
    doc_type: str,
    out_path: str | Path | None = None,
    *,
    order: Order | None = None,
    parcel_id: str | None = None,
) -> Document:
    """Render a document: gate -> Jinja2 -> WeasyPrint -> sha256 -> new row.

    Args:
        document_data: DocumentData (or dict shaped like it — model_validate).
        doc_type: one of FORM_TYPES.
        out_path: PDF destination (default ``docs-out/{doc_type}-v{version}.pdf``).
        order: optional Order with line_items — when provided and order has
            multiple line_items for INVOICE/PACKING_LIST, delegates to
            ``render_line_items()`` and returns the first Document row.

    Returns:
        The persisted ``Document`` row (version 1, 2, … — never overwritten).

    Raises:
        ValueError: unknown ``doc_type`` or form-type mismatch.
        ValidationError: ``DocumentData`` shape invalid, an official
            filling-rule rejection (pbe-iii-iv-fields.md §7) or required
            pbe_field_schemas fields missing (all raised BEFORE WeasyPrint).
    """
    if order is not None and len(order.line_items) > 1 and doc_type in ("INVOICE", "PACKING_LIST") and parcel_id is None:
        results = render_line_items(order, doc_type, out_dir=out_path)
        return results[0] if results else render(document_data, doc_type, out_path)

    data = DocumentData.model_validate(document_data)
    if doc_type not in _TEMPLATE_FILE:
        raise ValueError(f"unknown doc_type {doc_type!r} — expected one of {list(FORM_TYPES)}")
    if data.form_type != doc_type:
        raise ValueError(
            f"doc_type {doc_type!r} does not match DocumentData.form_type {data.form_type!r}"
        )
    # Official filling-rule gate (todo 14): reject with the portal's exact
    # strings BEFORE WeasyPrint; restricted-policy ITCH codes warn, never block.
    rules = validate_document_rules(data)
    for warning in rules.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if rules.errors:
        _raise_rules_error(rules.errors)
    _gate_completeness(data, doc_type)
    # SDR enforcement gate: the CN22/CN23 label is derived from the declared
    # value (300-SDR threshold), never user-picked.  On a mismatch the form is
    # auto-switched — the CLI/preview note names the switch and the
    # ``documents`` row records the ACTUAL rendered doc_type.
    resolved_doc_type, data = _resolve_cn_label(data, doc_type)
    if resolved_doc_type != doc_type:
        print(_cn_switch_note(doc_type, resolved_doc_type, data.value_minor))
        doc_type = resolved_doc_type

    html = build_html(data, doc_type)
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    checksum = _checksum(pdf_bytes)
    version, supersedes = _next_version(doc_type)
    if parcel_id is not None:
        file_base = f"{doc_type}-{parcel_id}-v{version}.pdf"
    else:
        file_base = f"{doc_type}-v{version}.pdf"
    path = Path(out_path) / file_base if out_path is not None and Path(out_path).is_dir() else (Path(out_path) if out_path is not None else DOCS_OUT / file_base)
    # If out_path is a file-like path containing suffix, respect it but ensure parcel suffix
    if out_path is not None and Path(out_path).suffix == ".pdf" and parcel_id is not None and parcel_id not in Path(out_path).name:
        stem = Path(out_path).stem
        path = Path(out_path).with_name(f"{stem}-{parcel_id}.pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf_bytes)

    structured = data.model_dump(mode="json")
    if parcel_id is not None:
        structured["parcel_id"] = parcel_id
    with SessionLocal() as session:
        row_kwargs: dict = {
            "doc_type": doc_type,
            "version": version,
            "checksum": checksum,
            "structured_json": structured,
            "file_path": str(path),
            "supersedes_doc_id": supersedes,
        }
        if parcel_id is not None and getattr(Document, "parcel_id", None) is not None:
            row_kwargs["parcel_id"] = parcel_id
        row_kwargs.update(_order_id_kwargs(order))
        row = Document(**row_kwargs)  # type: ignore[arg-type]
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


__all__ = ["build_html", "build_preview", "render", "render_line_items", "sdr_info"]
