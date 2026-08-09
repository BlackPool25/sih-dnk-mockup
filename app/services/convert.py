"""CLI to convert corpus research files into database config tables.

Usage:
    uv run python -m app.services.convert --lanes

Subcommands (build order):
    --lanes        import ITPS (135 countries) + EMS (4 markets) lane configs  [this todo]
    --categories   product categories            (todo 7)
    --states       state sales tax               (todo 7)
    --flags        config flags                  (todo 7)
    --pbe          PBE field schemas             (todo 7)
    --all          serial re-seed of every table (todo 12) — RESERVED, do not use

Every rate is a config flag with a source URL + level + verified timestamp,
never a bare number (corpus honesty rule FR-001).  Money is stored in
integer minor units (paise): ₹1 = 100.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import text

from app.db import SessionLocal
from app.models import Lane
from app.parsers.iso2 import UnmappedCountryError, to_iso2
from app.parsers.markdown_tables import parse_minor, parse_table

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# --- ITPS (L1: S.O. 659(E), Gazette of India, 6-Feb-2026) --------------------

ITPS_TABLE_FILE = DATA_DIR / "05-itps-ems-lanes" / "itps-full-rate-table-s0659e.md"
ITPS_EXPECTED_ROWS = 135  # Table VIII row-count gate (trailing prose must never be parsed)
ITPS_GAZETTE_URL = "https://archive.org/details/in.gazette.central.e.2026-02-06.269951"
ITPS_GAZETTE_DATE = date(2026, 2, 6)

# Weight caps — RESOLVED overrides (itps-lane.md §5).  The table file's own
# line-147 note ("2 kg for USA…") is STALE: DoP OM CF-71/17/2025-CF-DOP
# 01-Jan-2026 raised USA 2 kg → 5 kg (O10 resolved; USA shipping.md §1.3).
# NULL = unverified — never guessed from the "~29 destinations" list.
ITPS_WEIGHT_CAP_G: dict[str, int] = {
    "US": 5000,  # DoP OM 01-Jan-2026 (L1) + Shiprocket 21-Jan-2026 corroborates
    "AU": 2000,  # L1 gazette per-destination + PO Rules §50E
    "CA": 2000,  # L1 gazette per-destination
    "GB": 2000,  # per Table VIII convention (UK shipping.md §2.2; row not individually verified)
    "AE": 5000,  # DoP OM table (UAE shipping.md §2.1)
    "SG": 5000,  # DoP OM table (UAE shipping.md §2.1 lists Singapore max 5 kg)
}

# Transit ranges — L5, ranges only, ONLY where the corpus gives them
# (itps-lane.md §6): USA 18–28 · UK/EU ~16–25 · Gulf ~14–21 · AU ~18–28.
ITPS_TRANSIT_DAYS: dict[str, tuple[int, int]] = {
    "US": (18, 28),
    "GB": (16, 25),
    "AE": (14, 21),
    "AU": (18, 28),
}

# --- EMS (L5 estimates, corpus contradiction C11 — no authoritative         ---
# --- Schedule I public; conflicts kept verbatim, never averaged)            ---

EMS_SOURCE_FILES: dict[str, str] = {
    "US": "data/01-countries/USA/shipping.md",
    "GB": "data/01-countries/UK/shipping.md",
    "AE": "data/01-countries/UAE/shipping.md",
    "AU": "data/01-countries/Australia/shipping.md",
}

# (country name, spec) — rates in paise; transit in working days;
# `alternatives` = the C-1..C-4 conflicting published figures verbatim
# (ems-lane.md §4.2 + per-market shipping.md), key REQUIRED by todo 8.
EMS_MARKETS: list[tuple[str, dict[str, object]]] = [
    (
        "United States of America",
        {
            "first": 86500,  # working figure: corpus §4.2 + indiapost.org (L5)
            "addl": 10000,
            "transit": (5, 14),  # USA shipping.md §2.4
            "alternatives": [
                {"source": "clickpost", "first": 182000, "addl": 15000},  # USA shipping.md §2.1
                {"source": "findpincode", "first": 58500, "addl": None},  # ems-lane.md §4.2
            ],
        },
    ),
    (
        "United Kingdom",
        {
            "first": 86500,  # working figure: corpus §4.2 + indiapost.org (L5)
            "addl": 10000,
            "transit": (4, 14),  # UK shipping.md §4
            "alternatives": [
                {"source": "findpincode", "first": 95500, "addl": 10500},  # UK shipping.md §3.1
                {"source": "clickpost", "first": 196500, "addl": 9000},  # UK shipping.md §3.1
            ],
        },
    ),
    (
        "United Arab Emirates",
        {
            "first": 60000,  # working figure (corpus; UAE range ₹600–1,400 across sources)
            "addl": 4000,
            "transit": (3, 8),  # UAE shipping.md §3 / §4
            "alternatives": [
                {"source": "findpincode", "first": 89500, "addl": 5000},  # UAE shipping.md §3
                {"source": "indspeedpost", "first": 124000, "addl": 5000},  # UAE shipping.md §3
                {"source": "shiprocket", "first": 60000, "addl": 6000},  # UAE shipping.md §3
                {"source": "clickpost", "first": 140000, "addl": 4000},  # UAE shipping.md §3
            ],
        },
    ),
    (
        "Australia",
        {
            "first": 63000,  # working figure: PO Rules §225 + indiapost.org (L5)
            "addl": 15500,
            "transit": (5, 14),  # Australia shipping.md §3
            "alternatives": [
                {"source": "clickpost", "first": 112500, "addl": 23000},  # AU shipping.md §2.1
            ],
        },
    ),
]

VERIFIED_AT = datetime(2026, 8, 8, tzinfo=UTC)  # corpus snapshot date


# --- importers ---------------------------------------------------------------


def _itps_lanes() -> list[Lane]:
    """Parse the 135-row ITPS table into Lane rows.

    Raises UnmappedCountryError on any country name that cannot be mapped
    to ISO-3166-1 (the 135/135 gate) and RuntimeError on any row-count
    mismatch — trailing prose after the table can never become rows.
    """
    rows = parse_table(ITPS_TABLE_FILE.read_text(encoding="utf-8").splitlines())
    lanes: list[Lane] = []
    for row in rows:
        if "Country" not in row:
            continue  # defensive: only the gazette table carries a Country column
        name = row["Country"]
        first_minor = parse_minor(row["First 50g (₹)"])
        addl_minor = parse_minor(row["Each addl 50g (₹)"])
        if first_minor is None or addl_minor is None:
            raise ValueError(f"missing rate in ITPS row {row.get('#')!r}: {name!r}")
        iso2 = to_iso2(name)  # raises UnmappedCountryError — the 135/135 gate
        transit = ITPS_TRANSIT_DAYS.get(iso2)
        lanes.append(
            Lane(
                lane="ITPS",
                country_iso2=iso2,
                first_slab_g=50,
                first_slab_rate_minor=first_minor,
                addl_slab_g=50,
                addl_slab_rate_minor=addl_minor,
                weight_cap_g=ITPS_WEIGHT_CAP_G.get(iso2),  # NULL = unverified
                volume_free=True,  # ITPS bills ACTUAL weight only (itps-lane.md §4)
                divisor=None,
                transit_min_days=transit[0] if transit else None,
                transit_max_days=transit[1] if transit else None,
                conflicts=None,
                source_url=ITPS_GAZETTE_URL,
                source_level="L1",
                confidence="high",
                is_estimate=False,
                effective_from=ITPS_GAZETTE_DATE,
                verified_at=VERIFIED_AT,
            )
        )
    if len(lanes) != ITPS_EXPECTED_ROWS:
        raise RuntimeError(
            f"ITPS row-count gate failed: parsed {len(lanes)} rows, "
            f"expected {ITPS_EXPECTED_ROWS}"
        )
    return lanes


def _ems_lanes() -> list[Lane]:
    """Build the 4 EMS Lane rows for US/GB/AE/AU from the corpus shipping files."""
    lanes: list[Lane] = []
    for name, spec in EMS_MARKETS:
        iso2 = to_iso2(name)
        transit = spec["transit"]  # type: ignore[assignment]
        lanes.append(
            Lane(
                lane="EMS",
                country_iso2=iso2,
                first_slab_g=250,
                first_slab_rate_minor=spec["first"],  # type: ignore[arg-type]
                addl_slab_g=250,
                addl_slab_rate_minor=spec["addl"],  # type: ignore[arg-type]
                weight_cap_g=None,  # no authoritative per-market ceiling (C11/C16)
                volume_free=False,  # EMS may bill volumetric (PO Regs 2024 clause (r))
                divisor=None,  # no official international divisor (÷4000/5000/6000 conflict)
                transit_min_days=transit[0],
                transit_max_days=transit[1],
                conflicts={"alternatives": spec["alternatives"]},
                source_url=EMS_SOURCE_FILES[iso2],
                source_level="L5",
                confidence="low",
                is_estimate=True,
                verified_at=VERIFIED_AT,
            )
        )
    return lanes


def import_lanes() -> tuple[int, int]:
    """Seed ``lanes`` with ITPS (135) + EMS (4) — idempotent.

    TRUNCATE (no CASCADE — ``lanes`` has no inbound FKs) + insert run in
    ONE transaction, so re-runs never duplicate and a failure leaves the
    table untouched.  The ISO2 gate runs before the DB is touched.
    """
    itps = _itps_lanes()  # raises before any DB write if any name is unmapped
    ems = _ems_lanes()
    with SessionLocal.begin() as session:
        session.execute(text("TRUNCATE TABLE lanes"))
        session.add_all(itps + ems)
    return len(itps), len(ems)


# --- stub subcommands (built in later todos) ---------------------------------


def _stub(flag: str, todo: str) -> Callable[[], str]:
    def run() -> str:
        return f"--{flag}: not implemented yet (todo {todo}); nothing imported"

    return run


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
    parser.add_argument(
        "--all",
        action="store_true",
        help="serial re-seed of every table (RESERVED for todo 12 — do not use)",
    )
    args = parser.parse_args(argv)

    subcommands: list[tuple[str, Callable[[], object]]] = [
        ("lanes", import_lanes),
        ("categories", _stub("categories", "7")),
        ("states", _stub("states", "7")),
        ("flags", _stub("flags", "7")),
        ("pbe", _stub("pbe", "7")),
        ("all", _stub("all", "12")),
    ]
    chosen = [(flag, fn) for flag, fn in subcommands if getattr(args, flag)]
    if not chosen:
        parser.error("no subcommand given — use --lanes")
    if len(chosen) > 1:
        parser.error("pass exactly one subcommand at a time (--all is reserved for todo 12)")

    _, fn = chosen[0]
    try:
        result = fn()
    except UnmappedCountryError as exc:
        print(f"error: ISO2 gate failed: {exc}", file=sys.stderr)
        return 1
    if isinstance(result, tuple):
        itps, ems = result
        print(f"imported {itps} ITPS + {ems} EMS = {itps + ems} lanes")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
