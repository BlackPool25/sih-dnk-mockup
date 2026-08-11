"""Seed package — one module per config domain, plus the orchestration
(CONFIG_TABLES / _config_truncate / import_configs) and the CLI (main).

A subcommand's WHOLE set is truncated together in ONE statement: hs_codes
FKs to product_categories, so Postgres rejects truncating either alone.
state_sales_tax / config_flags / pbe_field_schemas / filling_rules have no
inbound FKs and may be truncated alone.  ``lanes`` is deliberately excluded:
todo 6 owns it.

``app.services.convert`` is a thin facade re-exporting ``import_configs`` /
``import_lanes`` / ``main`` — ``python -m app.services.convert`` keeps
working unchanged.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import text

from app.db import SessionLocal
from app.parsers.iso2 import UnmappedCountryError
from app.services.seed.categories import _import_categories
from app.services.seed.flags import _import_flags
from app.services.seed.lanes import import_lanes
from app.services.seed.pbe import _import_pbe
from app.services.seed.rules import _import_rules
from app.services.seed.states import _import_states

# --- todo 7: categories / states / flags / pbe / rules --------------------------
#
# One transaction: a dynamic TRUNCATE of exactly the tables the selected
# subcommands re-seed (single statement — hs_codes FKs to product_categories,
# so ``--categories`` truncates product_categories + hs_codes + country_rates
# together, while ``--states``/``--flags``/``--pbe``/``--rules`` truncate only
# their own table), then insert.  Re-runs never duplicate.  ``lanes`` is not
# touched.


# Subcommand -> the tables it re-seeds.  A subcommand's WHOLE set is truncated
# together in ONE statement: hs_codes FKs to product_categories, so Postgres
# rejects truncating either alone.  state_sales_tax / config_flags /
# pbe_field_schemas have no inbound FKs and may be truncated alone.
CONFIG_TABLES: dict[str, tuple[str, ...]] = {
    "categories": ("product_categories", "hs_codes", "country_rates"),
    "states": ("state_sales_tax",),
    "flags": ("config_flags",),
    "pbe": ("pbe_field_schemas",),
    "rules": ("filling_rules",),
}


def _config_truncate(selected: set[str]) -> text:
    """One dynamic TRUNCATE of the union of tables the selected subcommands
    re-seed (single statement, RESTART IDENTITY — idempotent re-runs)."""
    tables: list[str] = []
    for sub in ("categories", "states", "flags", "pbe", "rules"):
        if sub in selected:
            tables.extend(CONFIG_TABLES[sub])
    unique: list[str] = []
    for t in tables:
        if t not in unique:
            unique.append(t)
    return text(f"TRUNCATE {', '.join(unique)} RESTART IDENTITY")


# --- combined todo-7 runner ----------------------------------------------------


def import_configs(
    *, categories: bool, states: bool, flags: bool, pbe: bool, rules: bool = False
) -> str:
    """Seed the selected todo-7 config tables in ONE transaction — idempotent.

    Only the tables the selected subcommands re-seed are truncated (dynamic
    single-statement TRUNCATE), so e.g. ``--pbe`` alone re-seeds only
    pbe_field_schemas and leaves the other config tables untouched.
    """
    selected = {name for name, on in (
        ("categories", categories), ("states", states), ("flags", flags),
        ("pbe", pbe), ("rules", rules),
    ) if on}
    with SessionLocal.begin() as session:
        if selected:
            session.execute(_config_truncate(selected))
        lines: list[str] = []
        if categories:
            n_cat, n_hs, n_rates = _import_categories(session)
            lines.append(f"imported {n_cat} product categories ({n_hs} hs codes, {n_rates} country rates)")
        if states:
            lines.append(f"imported {_import_states(session)} state sales-tax rows")
        if flags:
            n_flags, n_labels = _import_flags(session)
            lines.append(f"imported {n_flags} config flags ({n_labels} labels.*)")
        if pbe:
            n3, n4 = _import_pbe(session)
            lines.append(f"imported {n3 + n4} PBE field schemas (PBE_III {n3}, PBE_IV {n4})")
        if rules:
            lines.append(f"imported {_import_rules(session)} filling rules")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.services.convert",
        description="Convert corpus research files into database config tables.",
    )
    parser.add_argument("--lanes", action="store_true", help="seed lanes: ITPS 135 + EMS 4")
    parser.add_argument("--categories", action="store_true", help="seed product categories (todo 7)")
    parser.add_argument("--states", action="store_true", help="seed state sales tax (todo 7)")
    parser.add_argument("--flags", action="store_true", help="seed config flags (todo 7)")
    parser.add_argument("--pbe", action="store_true", help="seed PBE field schemas (todo 7)")
    parser.add_argument("--rules", action="store_true", help="seed filling rules (rework wave 0)")
    parser.add_argument(
        "--all",
        action="store_true",
        help="serial re-seed of every table: lanes (todo 6), then the seven "
        "config tables (todo 7) — idempotent, runs ALONE",
    )
    args = parser.parse_args(argv)

    todo7 = [flag for flag in ("categories", "states", "flags", "pbe", "rules") if getattr(args, flag)]

    if args.all:
        if args.lanes or todo7:
            parser.error("--all must run alone (it re-seeds every table serially)")
        try:
            itps, ems = import_lanes()
            print(f"imported {itps} ITPS + {ems} EMS = {itps + ems} lanes")
            print(import_configs(categories=True, states=True, flags=True, pbe=True, rules=True))
        except UnmappedCountryError as exc:
            print(f"error: ISO2 gate failed: {exc}", file=sys.stderr)
            return 1
        except (RuntimeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.lanes:
        if todo7:
            parser.error("--lanes must run alone (todo 6/7 write disjoint tables in parallel)")
        try:
            itps, ems = import_lanes()
        except UnmappedCountryError as exc:
            print(f"error: ISO2 gate failed: {exc}", file=sys.stderr)
            return 1
        print(f"imported {itps} ITPS + {ems} EMS = {itps + ems} lanes")
        return 0

    if not todo7:
        parser.error("no subcommand given — use --categories/--states/--flags/--pbe/--rules (or --lanes)")

    try:
        print(import_configs(
            categories="categories" in todo7,
            states="states" in todo7,
            flags="flags" in todo7,
            pbe="pbe" in todo7,
            rules="rules" in todo7,
        ))
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
