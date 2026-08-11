"""Verification module — run every row-count gate + spot check + conflict log
against the seeded DB, regenerate `seed/verification_report.md`, and exit
non-zero on ANY gate failure.

Usage:
    uv run python -m app.services.verify

Exit code semantics: 0 = ALL gates PASS · non-zero = at least one FAIL.

Gates (todo-8 spec):
    G1  lanes ITPS = 135                  G7  config_flags >= 40
    G2  lanes EMS = 4                     G8  pbe_field_schemas >= 30
    G3  EMS: 0 conflicts NULL + 0 is_estimate=false   (todo-6 tamper target)
    G4  state_sales_tax = 51              G9  0 ITPS lanes with NULL country_iso2
    G5  product_categories = 8            G10 every imported row has source_url
    G6  every category >= 1 hs_code + total hs_codes >= 24
    G11 spot checks (rates/cap/transit/flags)  G12 psql auth SELECT 1
    G13 filling_rules = 8

The report also carries the C-1..C-13 conflict log (each entry quoted with
BOTH values + sources) and a flagged-rows list (confidence=unverified or
is_estimate=true).  Conflicts are logged, never silently dropped.

The `alternatives` word in the report MUST come from here, printed from the
`alternatives` key of each EMS row's `lanes.conflicts` JSONB — the todo-8
acceptance grep depends on it (see _ems_conflict_log).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, or_, select

from app.db import DATABASE_URL, SessionLocal
from app.models import (
    ConfigFlag,
    CountryRate,
    FillingRule,
    HsCode,
    Lane,
    PbeFieldSchema,
    ProductCategory,
    StateSalesTax,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "seed" / "verification_report.md"

# --- gate expectations (todo-8 spec §4) --------------------------------------

ITPS_EXPECTED = 135
EMS_EXPECTED = 4
STATES_EXPECTED = 51
CATEGORIES_EXPECTED = 8
HS_CODES_MIN = 24
FLAGS_MIN = 40
PBE_MIN = 30
FILLING_RULES_EXPECTED = 8

# G11 spot checks: (iso2, first_slab_rate_minor, addl_slab_rate_minor)
ITPS_SPOT: dict[str, tuple[int, int]] = {
    "US": (40000, 3500),
    "GB": (20000, 2500),
    "AE": (18500, 1500),
    "AU": (39500, 4500),
}
US_CAP_G = 5000
US_TRANSIT = (18, 28)  # itps-lane.md §6 — ranges only
SPOT_FLAGS = ("us.usps_clearance_fee_minor", "us.s301.rate_pct")

# All config tables that carry the ProvenanceMixin.source_url column (G10).
SOURCE_URL_TABLES: list[tuple[str, object]] = [
    ("lanes", Lane),
    ("product_categories", ProductCategory),
    ("hs_codes", HsCode),
    ("country_rates", CountryRate),
    ("state_sales_tax", StateSalesTax),
    ("config_flags", ConfigFlag),
    ("pbe_field_schemas", PbeFieldSchema),
]

# EMS conflict labels C-1..C-4 by country (ems-lane.md §4.2 order).
EMS_CONFLICT_LABEL = {"US": 1, "GB": 2, "AE": 3, "AU": 4}


@dataclass
class Gate:
    """One checked gate: rendered as `name | PASS/FAIL | actual | expected`."""

    name: str
    passed: bool
    actual: str
    expected: str
    notes: list[str] = field(default_factory=list)

    def line(self) -> str:
        result = "PASS" if self.passed else "FAIL"
        return f"| {self.name} | **{result}** | {self.actual} | {self.expected} |"


def _count(session, model, *where) -> int:
    return session.scalar(select(func.count()).select_from(model).where(*where))


def _row_count_gates(session) -> list[Gate]:
    """G1..G9: the row-count and NULL-integrity gates."""
    gates: list[Gate] = []

    itps = _count(session, Lane, Lane.lane == "ITPS")
    gates.append(Gate("G1 lanes ITPS", itps == ITPS_EXPECTED, str(itps), str(ITPS_EXPECTED)))

    ems = _count(session, Lane, Lane.lane == "EMS")
    gates.append(Gate("G2 lanes EMS", ems == EMS_EXPECTED, str(ems), str(EMS_EXPECTED)))

    # G3 — the tamper-test target: EMS rows must ALWAYS carry their conflict
    # payload and must ALWAYS be flagged as estimates (L5, C11).
    ems_no_conflicts = _count(session, Lane, Lane.lane == "EMS", Lane.conflicts.is_(None))
    ems_not_estimate = _count(session, Lane, Lane.lane == "EMS", Lane.is_estimate.is_(False))
    gates.append(
        Gate(
            "G3 EMS conflicts IS NULL",
            ems_no_conflicts == 0,
            f"{ems_no_conflicts} of {ems}",
            "0",
        )
    )
    gates.append(
        Gate(
            "G3 EMS is_estimate=false",
            ems_not_estimate == 0,
            f"{ems_not_estimate} of {ems}",
            "0 (all EMS rows must be estimates, L5)",
        )
    )

    states = _count(session, StateSalesTax)
    gates.append(Gate("G4 state_sales_tax", states == STATES_EXPECTED, str(states), str(STATES_EXPECTED)))

    cats = _count(session, ProductCategory)
    gates.append(Gate("G5 product_categories", cats == CATEGORIES_EXPECTED, str(cats), str(CATEGORIES_EXPECTED)))

    per_cat = dict(
        session.execute(
            select(ProductCategory.slug, func.count(HsCode.id))
            .join(HsCode, HsCode.product_cat == ProductCategory.id, isouter=True)
            .group_by(ProductCategory.slug)
        ).all()
    )
    min_cat = min(per_cat.values())
    gates.append(
        Gate(
            "G6 every category >= 1 hs_code",
            min_cat >= 1,
            f"min={min_cat} ({min(per_cat, key=per_cat.get)})",
            ">= 1 per category",
        )
    )

    hs_total = _count(session, HsCode)
    gates.append(
        Gate("G6 total hs_codes", hs_total >= HS_CODES_MIN, str(hs_total), f">= {HS_CODES_MIN}")
    )

    flags = _count(session, ConfigFlag)
    gates.append(Gate("G7 config_flags", flags >= FLAGS_MIN, str(flags), f">= {FLAGS_MIN}"))

    pbe = _count(session, PbeFieldSchema)
    gates.append(Gate("G8 pbe_field_schemas", pbe >= PBE_MIN, str(pbe), f">= {PBE_MIN}"))

    null_iso2 = _count(session, Lane, Lane.lane == "ITPS", Lane.country_iso2.is_(None))
    gates.append(
        Gate("G9 ITPS NULL country_iso2", null_iso2 == 0, str(null_iso2), "0")
    )
    return gates


def _source_url_gate(session) -> list[Gate]:
    """G10: every imported row of every config table has a non-empty source_url."""
    gates: list[Gate] = []
    for table, model in SOURCE_URL_TABLES:
        empty = _count(session, model, or_(model.source_url.is_(None), model.source_url == ""))
        total = _count(session, model)
        gates.append(
            Gate(
                f"G10 {table} source_url non-empty",
                empty == 0,
                f"{empty} empty of {total}",
                "0 empty",
            )
        )
    return gates


def _spot_check_gate(session) -> list[Gate]:
    """G11: lane spot checks (itps-lane.md §4/§6 + duties-taxes.md flags)."""
    gates: list[Gate] = []

    itps_by_iso = {
        r.country_iso2: r
        for r in session.scalars(
            select(Lane).where(Lane.lane == "ITPS", Lane.country_iso2.in_(ITPS_SPOT))
        )
    }
    for iso, (first, addl) in ITPS_SPOT.items():
        row = itps_by_iso.get(iso)
        gates.append(
            Gate(
                f"G11 {iso} ITPS first_slab_rate_minor",
                row is not None and row.first_slab_rate_minor == first,
                str(row.first_slab_rate_minor) if row else "missing",
                str(first),
            )
        )
    us = itps_by_iso.get("US")
    gates.append(
        Gate(
            "G11 US ITPS addl_slab_rate_minor",
            us is not None and us.addl_slab_rate_minor == 3500,
            str(us.addl_slab_rate_minor) if us else "missing",
            "3500",
        )
    )
    gates.append(
        Gate(
            "G11 US ITPS weight_cap_g",
            us is not None and us.weight_cap_g == US_CAP_G,
            str(us.weight_cap_g) if us else "missing",
            str(US_CAP_G),
        )
    )
    transit_ok = us is not None and (
        us.transit_min_days, us.transit_max_days
    ) == US_TRANSIT
    gates.append(
        Gate(
            "G11 US ITPS transit 18..28 days",
            transit_ok,
            f"{us.transit_min_days}..{us.transit_max_days}" if us else "missing",
            f"{US_TRANSIT[0]}..{US_TRANSIT[1]}",
        )
    )

    found_keys = set(
        session.scalars(select(ConfigFlag.flag_key).where(ConfigFlag.flag_key.in_(SPOT_FLAGS)))
    )
    present = {k: k in found_keys for k in SPOT_FLAGS}
    for key in SPOT_FLAGS:
        gates.append(
            Gate(
                f"G11 flag {key} present",
                present[key],
                "present" if present[key] else "missing",
                "present",
            )
        )
    return gates


def _rules_gate(session) -> Gate:
    """G13: filling_rules seeded — count(*) == 8 (the rule catalog is fixed)."""
    n = _count(session, FillingRule)
    return Gate(
        "G13 filling_rules seeded",
        n == FILLING_RULES_EXPECTED,
        str(n),
        str(FILLING_RULES_EXPECTED),
    )


def _auth_gate() -> Gate:
    """G12: `psql "$DATABASE_URL" -c "SELECT 1;"` must exit 0 — proves the
    .env password actually matches the container.  Uses the project's own
    bin/psql shim first (it loads .env itself and talks to the docker
    container), then PATH psql, then the SQLAlchemy engine (same
    DATABASE_URL) as a last resort."""
    url = os.environ.get("DATABASE_URL", DATABASE_URL)
    shim = PROJECT_ROOT / "bin" / "psql"
    psql = str(shim) if shim.is_file() and os.access(shim, os.X_OK) else shutil.which("psql")
    if psql is not None:
        proc = subprocess.run(
            [psql, url, "-c", "SELECT 1;"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        actual = f"exit {proc.returncode}"
        if proc.returncode:
            actual += f": {proc.stderr.strip()[:160]}"
        return Gate("G12 psql auth SELECT 1", proc.returncode == 0, actual, "exit 0")
    try:
        with SessionLocal() as session:
            session.execute(select(1))  # trivial SELECT 1 via the engine
        return Gate("G12 psql auth SELECT 1", True, "engine SELECT 1 ok (no psql on PATH)", "exit 0")
    except Exception as exc:  # noqa: BLE001 — gate must report ANY auth failure
        return Gate("G12 psql auth SELECT 1", False, f"engine SELECT 1 failed: {exc}", "exit 0")


# --- C-5..C-13 + data-quality conflict notes ---------------------------------
# Every entry quotes BOTH conflicting values and their sources (honesty rule:
# conflicts are logged, never silently dropped).

STATIC_CONFLICT_NOTES: list[tuple[str, list[str]]] = [
    (
        "C-5 MPF wording contradiction — INVERTED wording between the two US files",
        [
            ("- data/01-countries/USA/duties-taxes.md §4.2: *\"EMS (Express Mail Service) parcels from "
            "India are subject to MPF\"* (header: \"MPF — **exempt for postal mail, EXCEPT Inbound EMS**\")."),
            ("- data/01-countries/USA/shipping.md §9:232: *\"Merchandise Processing Fee (MPF) | "
            "**Exempt for inbound EMS** (\\\"Inbound Express Mail service\\\" / \\\"Inbound EMS\\\")\"*."),
            ("- Both cite the same CBP E-Commerce FAQ yet reach inverted conclusions. DB flag "
            "`us.mpf.postal` = \"exempt_itps_liable_ems\" records the duties-taxes.md reading; "
            "resolve per item at build."),
        ],
    ),
    (
        "C-6/C-7 US ITPS cap — RESOLVED 5 kg (overrides the stale table-file note)",
        [
            ("- DoP OM CF-71/17/2025-CF-DOP, 01-Jan-2026 (L1): *\"maximum permissible weight limit for "
            "the United States of America under the ITPS mail category has also been increased from "
            "2 kg to 5 kg\"* (USA shipping.md §1.3; data/README.md freshness note; Shiprocket "
            "21-Jan-2026 corroborates)."),
            ("- Overrides the STALE note at data/05-itps-ems-lanes/itps-full-rate-table-s0659e.md "
            "line 147: *\"Weight caps: 2 kg for USA/Australia/Canada (top markets); 5 kg for ~29 "
            "destinations; per-table otherwise. O10 open question: US cap may have risen to 5 kg "
            "(Shiprocket Jan-2026 note) — verify at build.\"*"),
            ("- DB: US ITPS weight_cap_g = 5000; AU/CA/GB = 2000; AE/SG = 5000 (convert.py "
            "ITPS_WEIGHT_CAP_G)."),
        ],
    ),
    (
        "C-8 UK EMS 1 kg upper bound untraceable",
        [
            ("- data/01-countries/UK/duties-taxes.md (worked example): *\"postage EMS 1 kg ≈ "
            "₹1,165–₹2,275 (see shipping.md)\"*."),
            ("- UK shipping.md computes 1 kg EMS = ₹1,165 and 2 kg = ₹2,665 — the ₹2,275 upper bound "
            "matches NO arithmetic in either file. Untraceable; treat as a typo until re-checked."),
        ],
    ),
    (
        "C-9 AU EMS confidence-tier conflict",
        [
            ("- Working figure ₹630 + ₹155/250 g stored from PO Rules §225 (statutory mirror — L1-text) "
            "and indiapost.org (L5)."),
            ("- ClickPost 2026 quotes ₹1,125 + ₹230/250 g (AU shipping.md §2.1) — 1.8× higher; no "
            "authoritative Schedule I public (C11). Stored confidence=low, is_estimate=true."),
        ],
    ),
    (
        "C-10 USPS $9.35 clearance fee — L1 partial",
        [
            ("- Federal Register 91:603, 8-Jan-2026 (L1) sets the **competitive** customs clearance & "
            "delivery fee at $9.35 per dutiable item (USA shipping.md §9)."),
            ("- The amount applicable to the postal-inbound class (India Post parcels) is NOT "
            "L1-confirmed — shipping.md §9: \"Whether the $9.35 or the older ~$5 level applies to a "
            "given India Post parcel is not L1-confirmed for the postal-inbound class.\" "
            "DB flag `us.usps_clearance_fee_minor` = 935, confidence=high (fee level flagged at build)."),
        ],
    ),
    (
        "C-11 volumetric divisor — no official international figure",
        [
            ("- ÷6000 (courierbook Oct-2025; shipmozo; singhxpress) · ÷5000 (clickpost; courierbook "
            "Jan-2026 \"UPU standard alignment\"; costcalculator) · ÷4000 (smartfree) — corpus F-H5-c, "
            "82% High no-official-figure (ems-lane.md §5; USA shipping.md §4)."),
            ("- Domestic reference ÷5000 (DoP OM 11-Dec-2025, L1) sometimes misapplied to "
            "international. DB flag `volumetric.divisors` = [4000, 5000, 6000], "
            "confidence=unverified, is_estimate=true; EMS lanes divisor=NULL."),
        ],
    ),
    (
        "C-12 EMS weight caps 20/30/35 — unresolved claims",
        [
            "- Corpus C16 RESOLVED: Air Parcel 20 kg general (destination governs).",
            ("- 30 kg claims (indiapost.org 2026; ClickPost \"up to 30 kg\") vs legacy official table "
            "31.5 kg for a few (Barbados, Kenya, Macao, Nepal, Romania, USA, Vietnam) and 20 kg for "
            "some (Bahrain, Belarus, Iceland, Iran, Israel, Mexico, Mongolia, Nauru, Pakistan, "
            "Poland, Spain, Taiwan, Thailand, Tunisia, Ukraine, Yemen) (ems-lane.md §6)."),
            "- No authoritative per-market EMS ceiling fetched → EMS weight_cap_g = NULL (never guessed).",
        ],
    ),
    (
        "C-13 counter practice unverified",
        [
            ("- Whether India Post counters actually apply volumetric to bulky crafts is UNVERIFIED "
            "(corpus 60% Moderate; field instrument O4 settles it)."),
            ("- ClickPost (Jul-2026) counter-claim: \"India Post EMS charges on actual weight only…\" — "
            "a direct contradiction of PO Regs 2024 clause (r) (ems-lane.md §5). EMS lanes "
            "divisor=NULL until verified."),
        ],
    ),
    (
        "Postage-row data-quality flags (category docs vs gazette Table VIII)",
        [
            ("- jute-products/category-doc.md: \"300 g → USA ₹505\" — the gazette formula value at "
            "**200 g** (₹400 + 3×₹35 = ₹505); the 300 g row should be ₹575. Row mislabelled one slab "
            "(jute 300 g ≈ formula-200 g)."),
            ("- imitation-artisan-jewellery/category-doc.md: \"200 g → USA ₹470\" — the formula value "
            "at **150 g**; correct 200 g = ₹505. Row mislabelled one slab down (jewellery 200 g)."),
            ("- Both docs' UK columns shift the same way (jewellery UK 200 g ₹250 vs formula ₹275). "
            "Cosmetic examples only — the gazette formula in the DB is the source of truth."),
        ],
    ),
    (
        "IEC application fee ₹500-vs-free",
        [
            ("- data/02-dnk-documents/onboarding/onboarding-guide.md: \"₹500 application fee; e-Sign "
            "via Aadhaar (free) or DSC (vendor-priced)\"."),
            ("- data/02-dnk-documents/document-stack.md (flags): \"IEC fee 'free vs ₹500' (both appear "
            "in official sources)\". Both values logged; no DB flag pinned (council-set fee, "
            "re-check at build)."),
        ],
    ),
    (
        "Brass 8306.29 MFN Free-vs-not",
        [
            ("- small-brass-metalware/category-doc.md §3.4: \"8306.29.00.00 other statuettes = Free "
            "(MFN)\" — htshub shows Free; wove shows only China S.301 10%."),
            ("- Same section: \"The 8306.29 MFN = Free result is worth a build-time re-check (two "
            "aggregators conflict on effective vs statutory).\" Logged, not shipped as fact."),
        ],
    ),
    (
        "GSTIN hard-block H2 — contested",
        [
            ("- On paper no hard-block (70% Moderate): DGFT issues IEC without GSTIN (\"GSTIN … if "
            "applicable\", IEC Manual v2.0); PBE forms read \"GSTIN or as applicable\"; DNK SOP KYC "
            "Note-1 allows booking with IEC alone (document-stack.md)."),
            ("- BUT the DNK SOP business-details table marks GSTIN \"Mandatory\", and whether the "
            "migrated portal (app.indiapost.gov.in/customer-selfservice) honours the escape hatch "
            "is UNTESTED — if it diverges, the hard-block branch is restored (findings H2)."),
        ],
    ),
    (
        "FEMA 9-vs-15 month realisation",
        [
            ("- `fema.realisation_months` = 9: FEMA (Export of Goods and Services) (First Amendment) "
            "Regulations 2026, 5-Jun-2026 (taxguru)."),
            ("- `fema.relaxation_months` = 15: RBI press release 31-Mar-2026 relaxation window. Both "
            "live flags coexist; the 15-month window is the relaxation, not the base rule."),
        ],
    ),
    (
        "Wise e-FIRC $2-vs-$2.50",
        [
            ("- payment-rails.md §2.4: \"~US$2–2.50 e-FIRC fee\" vs \"the equivalent of US$2 in the "
            "requested currency per transfer (US$2.50 for USD)\"."),
            ("- DB flag `wise.efirc_fee_minor` = 200 ($2.00, non-USD corridors); USD transfers cost "
            "$2.50 — difference logged, not averaged."),
        ],
    ),
    (
        "Magnet threshold 4.6 m-vs-4.5 m",
        [
            ("- jewellery/category-doc.md §4.2: \"≤ 0.418 A/m (≈0.00525 gauss) **at 4.6 m**\" "
            "(radialmagnet, IATA PI 953) vs \"0.00525 gauss **at 4.5 m**\" (FAA PackSafe) — the same "
            "field limit quoted at two measurement distances."),
            ("- Neither blocks a magnet-free parcel; both cited in the doc; flagged as an open "
            "measurement discrepancy."),
        ],
    ),
]


def _ems_conflict_log(session) -> list[str]:
    """C-1..C-4: every EMS row (confidence=low, is_estimate=true) with the
    conflicting source values quoted VERBATIM from lanes.conflicts.

    The `alternatives` word below MUST come from the `alternatives` key of
    each EMS row's conflicts JSONB — todo-8's acceptance grep greps for it.
    """
    lines: list[str] = []
    ems_rows = list(
        session.scalars(select(Lane).where(Lane.lane == "EMS").order_by(Lane.country_iso2))
    )
    for row in ems_rows:
        label = EMS_CONFLICT_LABEL.get(row.country_iso2, "?")
        payload = row.conflicts or {}
        # Pinned: the literal key `alternatives` is printed from the JSONB —
        # the report must not contain the word from anywhere else.
        alternatives = payload.get("alternatives")
        lines.append(
            f"- **C-{label} {row.country_iso2} EMS** — confidence={row.confidence}, "
            f"is_estimate={row.is_estimate}; working figure ₹{row.first_slab_rate_minor / 100:g} "
            f"+ ₹{row.addl_slab_rate_minor / 100:g}/250 g (L5). Conflicting published figures "
            f"verbatim from `lanes.conflicts`:"
        )
        lines.append(f"  - `alternatives`: {json.dumps(alternatives, sort_keys=True)}")
        for alt in alternatives or []:
            addl = f"+ ₹{alt['addl'] / 100:g}/250 g" if alt.get("addl") else "(addl n/a)"
            lines.append(
                f"    - {alt['source']}: first 250 g ₹{alt['first'] / 100:g} {addl}"
            )
    return lines


def _flagged_rows(session) -> list[str]:
    """Every row with confidence=unverified OR is_estimate=true (honesty rule:
    estimates are never presented as facts)."""
    lines: list[str] = []
    for lane in session.scalars(
        select(Lane).where(or_(Lane.confidence == "unverified", Lane.is_estimate.is_(True)))
    ):
        lines.append(
            f"- lanes.{lane.lane}.{lane.country_iso2} — confidence={lane.confidence}, "
            f"is_estimate={lane.is_estimate}"
        )
    for rate in session.scalars(
        select(CountryRate).where(
            or_(CountryRate.confidence == "unverified", CountryRate.is_estimate.is_(True))
        )
    ):
        lines.append(
            f"- country_rates.{rate.country_iso2}.{rate.rate_type} "
            f"(hs6={rate.hs6 or '—'}) — confidence={rate.confidence}, is_estimate={rate.is_estimate}"
        )
    for flag in session.scalars(
        select(ConfigFlag).where(
            or_(ConfigFlag.confidence == "unverified", ConfigFlag.is_estimate.is_(True))
        )
    ):
        lines.append(
            f"- config_flags.{flag.flag_key} — confidence={flag.confidence}, "
            f"is_estimate={flag.is_estimate}"
        )
    return lines


def _render(gates: list[Gate], ems_log: list[str], flagged: list[str]) -> str:
    passed = sum(1 for g in gates if g.passed)
    total = len(gates)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# DNK Mockup — Verification Report",
        "",
        f"**Generated:** {now} · **Exit code:** 0 = ALL PASS, non-zero = ANY FAIL",
        "",
        "## Gates",
        "",
        "| Gate | Result | Actual | Expected |",
        "|---|---|---|---|",
        *[g.line() for g in gates],
        "",
        f"**{passed}/{total} gates PASS** — " + (
            "ALL GATES PASS" if passed == total else f"{total - passed} GATE(S) FAIL"
        ),
        "",
        "## Conflicts log (C-1..C-13 + data-quality flags)",
        "",
        "### C-1..C-4 — EMS conflicting published figures (verbatim from `lanes.conflicts`)",
        "",
        *ems_log,
        "",
    ]
    for label, note in STATIC_CONFLICT_NOTES:
        lines.append(f"### {label}")
        lines.append("")
        lines.extend(note)
        lines.append("")
    lines += [
        "## Flagged rows (confidence=unverified OR is_estimate=true)",
        "",
        *flagged,
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    del argv  # no CLI args today — gates are fixed by the todo-8 spec
    with SessionLocal() as session:
        gates = (
            _row_count_gates(session)
            + _source_url_gate(session)
            + _spot_check_gate(session)
        )
        ems_log = _ems_conflict_log(session)
        flagged = _flagged_rows(session)
        rules_gate = _rules_gate(session)
    gates.append(_auth_gate())
    gates.append(rules_gate)  # G13 runs after G12 in the report

    report = _render(gates, ems_log, flagged)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    passed = sum(1 for g in gates if g.passed)
    failed = len(gates) - passed
    print(f"verification report written: {REPORT_PATH}")
    for gate in gates:
        print(f"  {'PASS' if gate.passed else 'FAIL'}  {gate.name}  (actual={gate.actual})")
    print(f"{passed}/{len(gates)} gates passed — " + ("ALL PASS" if failed == 0 else f"{failed} FAILED"))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
