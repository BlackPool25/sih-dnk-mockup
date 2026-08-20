"""ITPS (135) + EMS (4) lane seeds (todo 6) — TRUNCATE + insert in ONE
transaction, idempotent.  The ISO2 gate runs before the DB is touched.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text

from app.db import SessionLocal
from app.models import Lane
from app.parsers.iso2 import to_iso2
from app.parsers.markdown_tables import parse_minor, parse_table
from app.services.seed._common import DATA_DIR, VERIFIED_AT

# --- ITPS (L1: S.O. 659(E), Gazette of India, 6-Feb-2026) --------------------

ITPS_TABLE_FILE = DATA_DIR / "05-itps-ems-lanes" / "itps-full-rate-table-s0659e.md"
ITPS_EXPECTED_ROWS = 135  # Table VIII row-count gate (trailing prose must never be parsed)
ITPS_GAZETTE_URL = "https://archive.org/details/in.gazette.central.e.2026-02-06.269951"
ITPS_GAZETTE_DATE = date(2026, 2, 6)

# Weight caps — RESOLVED overrides (itps-lane.md §5).
# Unified ITPS 5 kg (5000g) for US/GB/AE/AU per S.O. gazette + EMS Schedule I
# update (2026-02-06 + DoP OM 01-Jan-2026).  Previous per-destination 2 kg
# values for AU/GB/CA were stale and are now superseded.
# NULL = unverified — never guessed from the "~29 destinations" list.
ITPS_WEIGHT_CAP_G: dict[str, int] = {
    "US": 5000,  # United States — ITPS Limit 5 kg (S.O. gazette + DoP OM L1)
    "GB": 5000,  # United Kingdom — ITPS Limit 5 kg (Schedule I)
    "AE": 5000,  # United Arab Emirates — ITPS Limit 5 kg (DoP OM table)
    "AU": 5000,  # Australia — ITPS Limit 5 kg (stricter EMS cap is separate)
    "CA": 2000,  # Canada — L1 gazette per-destination (unchanged)
    "SG": 5000,  # Singapore — DoP OM table (UAE shipping.md §2.1 lists Singapore max 5 kg)
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
EMS_CAPS_G: dict[str, int] = {
    "US": 31500,
    "GB": 30000,
    "AE": 30000,
    "AU": 20000,
}

EMS_MARKETS: list[tuple[str, dict[str, object]]] = [
    (
        "United States of America",
        {
            "first": 86500,
            "addl": 10000,
            "weight_cap_g": 31500,
            "transit": (5, 14),
            "alternatives": [
                {"source": "clickpost", "first": 182000, "addl": 15000},
                {"source": "findpincode", "first": 58500, "addl": None},
            ],
        },
    ),
    (
        "United Kingdom",
        {
            "first": 86500,
            "addl": 10000,
            "weight_cap_g": 30000,
            "transit": (4, 14),
            "alternatives": [
                {"source": "findpincode", "first": 95500, "addl": 10500},
                {"source": "clickpost", "first": 196500, "addl": 9000},
            ],
        },
    ),
    (
        "United Arab Emirates",
        {
            "first": 60000,
            "addl": 4000,
            "weight_cap_g": 30000,
            "transit": (3, 8),
            "alternatives": [
                {"source": "findpincode", "first": 89500, "addl": 5000},
                {"source": "indspeedpost", "first": 124000, "addl": 5000},
                {"source": "shiprocket", "first": 60000, "addl": 6000},
                {"source": "clickpost", "first": 140000, "addl": 4000},
            ],
        },
    ),
    (
        "Australia",
        {
            "first": 63000,
            "addl": 15500,
            "weight_cap_g": 20000,
            "transit": (5, 14),
            "alternatives": [
                {"source": "clickpost", "first": 112500, "addl": 23000},
            ],
        },
    ),
]

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
                weight_cap_g=spec["weight_cap_g"],  # type: ignore[arg-type]
                volume_free=False,
                divisor=5000,
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
