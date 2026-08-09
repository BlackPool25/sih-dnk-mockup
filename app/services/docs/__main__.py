"""CLI for the document generation pipeline (todo 11).

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

Exit codes:
    0  rendered (or preview printed with --yes).
    1  invalid shipment / missing required fields / lane error /
       confirm required (--preview without --yes).
    2  argparse usage error.

Validity is deterministic-only: ``validate_shipment`` (business rules),
``DocumentData.model_validate`` (shape) and ``missing_required``
(completeness per pbe_field_schemas.required) — the LLM never validates.
"""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from pydantic import ValidationError

from app.schemas.shipment import Shipment
from app.services.docs.document import FORM_TYPES, DocumentData, build_document_data
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


def _ask_optional(data: DocumentData, args: argparse.Namespace) -> DocumentData:
    """Prompt for the optional order fields; declined values stay omitted
    (rendered "—").  EOF-safe so non-interactive runs fall back to omitted."""
    print("Optional order details (press Enter to omit — renders as '—'):")
    updates: dict = {}
    if args.consignee is None:
        try:
            value = input("Consignee name/address [empty]: ").strip()
        except EOFError:
            value = ""
        if value:
            updates["consignee"] = value
    if args.value_minor is None:
        try:
            raw = input("Declared value (INR minor units) [empty]: ").strip()
        except EOFError:
            raw = ""
        if raw:
            try:
                updates["value_minor"] = int(raw)
            except ValueError:
                print(
                    "error: declared value must be an integer (INR minor units) — omitted",
                    file=sys.stderr,
                )
    if not updates:
        print("  (no optional fields supplied — will render as '—')")
    return data.model_copy(update=updates)


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

    # 2. Completeness gate (pbe_field_schemas.required) — fails BEFORE any
    #    lookup or rendering; the missing pbe fields are listed.
    missing = missing_required(shipment, args.form)
    if missing:
        _error("cannot render — required fields missing: " + ", ".join(missing))

    # 3. Assemble DocumentData from DB lookups + validated Shipment keys +
    #    CLI order fields.
    try:
        data = build_document_data(
            shipment,
            args.form,
            consignee=args.consignee,
            value_minor=args.value_minor,
        )
    except (LookupError, ValueError, ValidationError) as exc:
        if isinstance(exc, ValidationError):
            _print_validation_error(exc, "error: invalid document data:")
        _error(str(exc))

    # 4. Optional details — ask the user before preview/render.
    if args.ask_optional:
        data = _ask_optional(data, args)

    # 5. Preview gate — the form summary + hi/kn confirm labels are shown;
    #    no PDF is written unless the user confirms with --yes.
    if args.preview:
        print(build_preview(data))
        if not args.yes:
            print(
                "confirm required: re-run with --yes to write the PDF", file=sys.stderr
            )
            return 1

    # 6. Render: gate -> Jinja2 -> WeasyPrint -> sha256 -> immutable row.
    try:
        doc = render(data, args.form, out_path=args.out)
    except ValidationError as exc:
        _print_validation_error(exc, "error: cannot render — required fields missing:")
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
    render_p.add_argument(
        "--form", choices=FORM_TYPES, required=True, help="form type to render"
    )
    render_p.add_argument(
        "--out", default=None, help="output PDF path (default docs-out/)"
    )
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
    render_p.add_argument(
        "--yes", action="store_true", help="confirm the preview and render"
    )
    render_p.add_argument(
        "--value-minor",
        type=int,
        default=None,
        help="optional declared value (INR minor units)",
    )
    render_p.add_argument(
        "--consignee", default=None, help="optional consignee name/address"
    )
    render_p.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
