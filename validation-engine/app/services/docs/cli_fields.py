"""DB-driven CLI field flags (wave 4) — every pbe_field_schemas field is
CLI-reachable via an auto-generated argparse flag (F5/R3).

Field keys that already have a legacy flag are RESERVED and never get an
auto flag; ``value_type == "auto"`` fields (boe_no) are skipped.  Money
fields get a ``-minor`` flag suffix (INR minor units — the project's money
convention); number fields take int; boolean and string-with-options fields
take choices from the DB row's options JSON.
"""

from __future__ import annotations

from sqlalchemy import select

from app.db import SessionLocal
from app.models import PbeFieldSchema

# Field keys already fed by the 13 legacy CLI flags — never auto-generated.
RESERVED_FIELDS: frozenset[str] = frozenset(
    {
        "product_description",
        "cth",
        "quantity_unit",
        "gross_weight",
        "net_weight",
        "destination_country",
        "consignee_details",
        "assessable_value",
        "amount_inr",
        "fob_value",
        "currency",
        "iec",
        "gstin_or_as_applicable",
    }
)

# The 8 dedicated rule-input/sender flags added alongside the auto flags.
DEDICATED_FLAGS: frozenset[str] = frozenset(
    {
        "--net-weight",
        "--fob",
        "--unit-value",
        "--piece-gross",
        "--sender",
        "--sender-ref",
        "--non-delivery",
        "--num-invoices",
    }
)


def flag_name(field_key: str) -> str:
    """Base argparse flag for a field_key: "decl.drawback" -> "--decl-drawback"."""
    return "--" + field_key.replace("_", "-").replace(".", "-")


def field_flag_name(spec: dict) -> str:
    """Full flag name for one spec — money fields carry a "-minor" suffix."""
    name = flag_name(spec["field_key"])
    return name + "-minor" if spec["value_type"] == "money" else name


def pbe_field_specs() -> list[dict]:
    """One spec per CLI-reachable field: the union of PBE_III + PBE_IV rows.

    Deduped by field_key (both forms share most fields; the first row — the
    PBE_III id order — wins).  Rows the legacy flags or the "auto" value_type
    already cover are excluded.  The DB stores a JSON null literal on rows
    WITHOUT options — detect via ``(row.options or {}).get("values")``.
    """
    with SessionLocal() as session:
        rows = session.scalars(select(PbeFieldSchema).order_by(PbeFieldSchema.id)).all()
    specs: dict[str, dict] = {}
    for row in rows:
        if row.field_key in specs:
            continue
        if row.value_type == "auto" or row.field_key in RESERVED_FIELDS:
            continue
        specs[row.field_key] = {
            "field_key": row.field_key,
            "value_type": row.value_type,
            "options": (row.options or {}).get("values"),
            "label": row.label,
        }
    return list(specs.values())


def add_pbe_field_arguments(parser) -> None:
    """Register one argparse argument per CLI-reachable pbe_field_schemas field.

    dest is the raw field_key (e.g. ``decl.drawback``); money flags take int
    minor units; boolean and string-with-options flags take the DB choices.
    """
    for spec in pbe_field_specs():
        key = spec["field_key"]
        kwargs: dict = {"dest": key, "help": f"{spec['label']} (DB field {key})"}
        vt = spec["value_type"]
        if vt in ("money", "number"):
            kwargs["type"] = int
        elif vt == "boolean":
            kwargs["choices"] = spec["options"] or ["Yes", "No", "NA"]
        elif vt == "string" and spec["options"]:
            kwargs["choices"] = spec["options"]
        parser.add_argument(field_flag_name(spec), **kwargs)


def collect_field_values(args) -> dict:
    """The provided auto-flag values: field_key -> value (None omitted)."""
    return {
        spec["field_key"]: getattr(args, spec["field_key"])
        for spec in pbe_field_specs()
        if getattr(args, spec["field_key"]) is not None
    }


__all__ = [
    "DEDICATED_FLAGS",
    "RESERVED_FIELDS",
    "add_pbe_field_arguments",
    "collect_field_values",
    "field_flag_name",
    "flag_name",
    "pbe_field_specs",
]
