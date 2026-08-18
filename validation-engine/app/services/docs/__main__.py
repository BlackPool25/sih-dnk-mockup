"""CLI for the document generation pipeline (todo 11, wave 4).

Usage:
    uv run python -m app.services.docs render \\
        --category embroidered-home-textiles --qty 8 --weight-g 400 \\
        --country US --form PBE_IV --out docs-out/pbe_sample.pdf

Flags:
    --preview        print the form summary (incl. hi/kn confirm labels) and
                     exit WITHOUT writing a PDF unless --yes is also passed.
    --ask-optional   prompt for the optional order fields (--consignee,
                     --value-minor) before rendering; declined = rendered "—".
    --yes            confirm the preview and write the PDF.
    --value-minor    optional declared value (INR minor units).
    --consignee      optional consignee name/address.
    --iec            exporter IEC — the DGFT/KYC gate requires ≥1 of IEC/GSTIN.
    --gstin          exporter GSTIN (15-char; gates alongside --iec).

Wave-4 additions:
    --net-weight     net weight in grams (rule input: gross ≤ 110% of net).
    --fob            FOB value in INR minor units (rule input: FOB ≤ invoice).
    --unit-value     unit value in INR minor units (Σ sub-piece value rule).
    --piece-gross    piece gross weight in grams (Σ sub-piece weight rule).
    --sender/--sender-ref/--non-delivery/--num-invoices — the CN22/CN23
                     sender block.
    --<db-field>     ONE auto-generated flag per remaining pbe_field_schemas
                     field (e.g. --exporter-name, --state-code,
                     --decl-drawback, --scheme-code) — derived from the DB;
                     money fields take INR MINOR units and carry a "-minor"
                     suffix (--export-duty-amount-minor).  Run
                     ``--help`` on the render subcommand to list them.

Exit codes:
    0  rendered (or preview printed with --yes).
    1  invalid shipment / missing required fields / official filling-rule
       rejection (e.g. "DGFT registration data missing") / lane error /
       confirm required (--preview without --yes).
    2  argparse usage error.

Validity is deterministic-only: ``validate_shipment`` (business rules),
``DocumentData.model_validate`` (shape), ``validate_document_rules`` (the
official PBE/CN22 filling rules, DB-driven) and ``missing_required``
(completeness per pbe_field_schemas.required) — the LLM never validates.
"""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from pydantic import ValidationError

from app.schemas.shipment import Shipment
from app.services.docs.cli_fields import add_pbe_field_arguments, collect_field_values
from app.services.docs.document import (
    FORM_TYPES,
    DocumentData,
    SenderBlock,
    build_document_data,
)
from app.services.docs.renderer import build_preview, render
from app.services.validate import missing_required, validate_shipment


def _error(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def _print_validation_error(exc: ValidationError, heading: str) -> NoReturn:
    print(heading, file=sys.stderr)
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        print(f"  - {loc}: {err['msg']}", file=sys.stderr)
    raise SystemExit(1)


def _build_data(
    shipment: Shipment,
    args: argparse.Namespace,
    *,
    consignee: str | None = None,
    value_minor: int | None = None,
) -> DocumentData:
    """Assemble the DocumentData from the shipment + ALL CLI flags (legacy,
    auto-generated DB fields, sender block, filling-rule inputs).

    ``consignee``/``value_minor`` override the CLI values (the prompted
    optional details are folded in by ``_prompt_optional``)."""
    if consignee is None:
        consignee = args.consignee
    if value_minor is None:
        value_minor = args.value_minor
    return build_document_data(
        shipment,
        args.form,
        consignee=consignee,
        value_minor=value_minor,
        iec=args.iec,
        gstin=args.gstin,
        field_values=collect_field_values(args),
        sender=SenderBlock(
            name_address=args.sender,
            sender_ref=args.sender_ref,
            non_delivery=args.non_delivery,
            num_invoices=args.num_invoices,
        ),
        net_weight_g=args.net_weight,
        fob_minor=args.fob,
        unit_value_minor=args.unit_value,
        piece_gross_g=args.piece_gross,
    )


def _prompt_optional(args: argparse.Namespace) -> tuple[str | None, int | None]:
    """Prompt for the optional order fields; declined values stay omitted
    (rendered "—").  EOF-safe so non-interactive runs fall back to omitted.
    Returns the final (consignee, value_minor) — flag values when given."""
    print("Optional order details (press Enter to omit — renders as '—'):")
    consignee = args.consignee
    if consignee is None:
        try:
            value = input("Consignee name/address [empty]: ").strip()
        except EOFError:
            value = ""
        consignee = value or None
    value_minor = args.value_minor
    if value_minor is None:
        try:
            raw = input("Declared value (INR minor units) [empty]: ").strip()
        except EOFError:
            raw = ""
        if raw:
            try:
                value_minor = int(raw)
            except ValueError:
                print(
                    "error: declared value must be an integer (INR minor units) — omitted",
                    file=sys.stderr,
                )
    if consignee is None and value_minor is None:
        print("  (no optional fields supplied — will render as '—')")
    return consignee, value_minor


def cmd_render(args: argparse.Namespace) -> int:
    # 1. Shipment from CLI order fields — deterministic business validation.
    try:
        shipment = Shipment(
            product_category=args.category,
            quantity=args.qty,
            weight_grams=args.weight_g,
            destination_country=args.country,
            confidence="high",
        )
        validate_shipment(shipment)
    except ValidationError as exc:
        _print_validation_error(exc, "error: invalid shipment:")

    # 2. Assemble DocumentData from DB lookups + validated Shipment keys +
    #    CLI order fields + auto-generated DB field flags.
    try:
        data = _build_data(shipment, args)
    except (LookupError, ValueError, ValidationError) as exc:
        if isinstance(exc, ValidationError):
            _print_validation_error(exc, "error: invalid document data:")
        _error(str(exc))

    # 3. Optional details — ask the user, then REBUILD with the prompted
    #    values so the derived field_values (assessable_value etc.) follow.
    if args.ask_optional:
        consignee, value_minor = _prompt_optional(args)
        data = _build_data(shipment, args, consignee=consignee, value_minor=value_minor)

    # 4. Completeness gate (pbe_field_schemas.required) — fails BEFORE the
    #    preview/render; the missing pbe fields are listed.
    missing = missing_required(data, args.form)
    if missing:
        _error("cannot render — required fields missing: " + ", ".join(missing))

    # 5. Preview gate — the form summary + hi/kn confirm labels are shown;
    #    no PDF is written unless the user confirms with --yes.
    if args.preview:
        print(build_preview(data))
        if not args.yes:
            print("confirm required: re-run with --yes to write the PDF", file=sys.stderr)
            return 1

    # 6. Render: gate -> Jinja2 -> WeasyPrint -> sha256 -> immutable row.
    try:
        doc = render(data, args.form, out_path=args.out)
    except ValidationError as exc:
        _print_validation_error(exc, "error: cannot render — document data rejected:")
    except ValueError as exc:
        _error(str(exc))
    print(f"document rendered: {doc.file_path}")
    print(f"checksum: {doc.checksum}")
    print(f"document id: {doc.id} (version {doc.version})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.services.docs",
        description="Deterministic document generation (Jinja2 + WeasyPrint).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render_p = sub.add_parser("render", help="render a customs/shipping document")
    render_p.add_argument("--category", required=True, help="product category slug")
    render_p.add_argument("--qty", type=int, required=True, help="quantity")
    render_p.add_argument(
        "--weight-g",
        dest="weight_g",
        type=int,
        required=True,
        help="gross/net weight in grams",
    )
    render_p.add_argument("--country", required=True, help="destination ISO2 code")
    render_p.add_argument("--form", choices=FORM_TYPES, required=True, help="form type to render")
    render_p.add_argument("--out", default=None, help="output PDF path (default docs-out/)")
    render_p.add_argument(
        "--preview",
        action="store_true",
        help="print form summary + hi/kn confirm labels, no PDF without --yes",
    )
    render_p.add_argument(
        "--ask-optional",
        action="store_true",
        help="prompt for optional order fields before rendering",
    )
    render_p.add_argument("--yes", action="store_true", help="confirm the preview and render")
    render_p.add_argument(
        "--value-minor",
        type=int,
        default=None,
        help="optional declared value (INR minor units)",
    )
    render_p.add_argument("--consignee", default=None, help="optional consignee name/address")
    render_p.add_argument(
        "--iec",
        default=None,
        help="exporter IEC (10-char) — the DGFT/KYC gate requires IEC or GSTIN",
    )
    render_p.add_argument(
        "--gstin",
        default=None,
        help="exporter GSTIN (15-char) — gates alongside --iec",
    )
    # Wave 4: the filling-rule inputs + sender block.
    render_p.add_argument(
        "--net-weight", type=int, default=None, help="net weight in grams (rule input)"
    )
    render_p.add_argument(
        "--fob", type=int, default=None, help="FOB value in INR minor units (rule input)"
    )
    render_p.add_argument(
        "--unit-value",
        type=int,
        default=None,
        help="unit value in INR minor units (sub-piece value rule)",
    )
    render_p.add_argument(
        "--piece-gross",
        type=int,
        default=None,
        help="piece gross weight in grams (sub-piece weight rule)",
    )
    render_p.add_argument("--sender", default=None, help="sender name and address")
    render_p.add_argument(
        "--sender-ref", default=None, help="sender's customs reference (e.g. IOSS)"
    )
    render_p.add_argument(
        "--non-delivery", default=None, help="non-delivery instruction (abandoned/return)"
    )
    render_p.add_argument(
        "--num-invoices",
        default=None,
        help="number of invoices/licenses/certificates",
    )
    # Wave 4: one auto-generated flag per remaining pbe_field_schemas field.
    add_pbe_field_arguments(render_p)
    render_p.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
