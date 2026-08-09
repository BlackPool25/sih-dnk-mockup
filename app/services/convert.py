"""CLI to convert corpus research files into database config tables.

Usage:
    uv run python -m app.services.convert --lanes
    uv run python -m app.services.convert --categories --states --flags --pbe

Subcommands (build order):
    --lanes        import ITPS (135 countries) + EMS (4 markets) lane configs  (todo 6 — runs ALONE)
    --categories   product categories + hs codes + country rates (todo 7)
    --states       state sales tax               (todo 7)
    --flags        config flags                  (todo 7)
    --pbe          PBE field schemas             (todo 7)
    --all          serial re-seed of EVERY table (todo 12): lanes, then the
                   six config tables, in one blocking run

The four todo-7 subcommands may be combined in ONE invocation; they share a
single transaction whose first statement is a combined TRUNCATE of the six
config tables (Postgres rejects truncating a referenced table unless every
referencing table is in the same statement — hs_codes FKs to
product_categories).  ``lanes`` is deliberately excluded: todo 6 owns it.

Every rate is a config flag with a source URL + level + verified timestamp,
never a bare number (corpus honesty rule FR-001).  Money is stored in
integer minor units (paise): ₹1 = 100.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import text

from app.db import SessionLocal
from app.models import (
    ConfigFlag,
    CountryRate,
    HsCode,
    Lane,
    PbeFieldSchema,
    ProductCategory,
    StateSalesTax,
)
from app.parsers.iso2 import UnmappedCountryError, to_iso2
from app.parsers.markdown_tables import parse_minor, parse_table, strip_markdown

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


# --- todo 7: categories / states / flags / pbe ----------------------------------
#
# One transaction: TRUNCATE the six config tables together (single statement —
# hs_codes FKs to product_categories, so truncating one alone is rejected),
# then insert.  Re-runs never duplicate.  ``lanes`` is not touched.

CATEGORY_DIR = DATA_DIR / "03-product-categories"
STATE_TAX_FILE = DATA_DIR / "01-countries" / "USA" / "state-sales-tax-table.md"
PBE_FIELDS_FILE = DATA_DIR / "02-dnk-documents" / "forms-pbe" / "pbe-iii-iv-fields.md"

CONFIG_TRUNCATE = text(
    "TRUNCATE product_categories, hs_codes, country_rates, state_sales_tax, "
    "config_flags, pbe_field_schemas RESTART IDENTITY"
)

SNAPSHOT_DATE = date(2026, 8, 8)

EMOJI_CONF = {"🟢": "high", "🟡": "moderate", "🔴": "low", "⚠️": "unverified"}
_EMOJI_RE = re.compile(r"[\u2600-\u27BF\u2B00-\u2BFF\U0001F000-\U0001FAFF\uFE0F]")
_MARKET_ISO2 = {"USA": "US", "UK": "GB", "UAE": "AE", "Australia": "AU"}
_MARKET_CURRENCY = {"US": "USD", "GB": "GBP", "AE": "AED", "AU": "AUD"}
_NO_STATE_NEXUS = {"OR", "NH", "MT", "DE", "AK"}  # no state-level sales-tax nexus


def _emoji_conf(text: str) -> str | None:
    for emoji, conf in EMOJI_CONF.items():
        if emoji in text:
            return conf
    return None


def _word_conf(text: str) -> str | None:
    if "Moderate" in text and "High" in text:
        return "moderate"
    if "High" in text:
        return "high"
    if "Moderate" in text:
        return "moderate"
    if "Low" in text:
        return "low"
    return None


def _clean(text: str) -> str:
    text = _EMOJI_RE.sub("", text)
    text = re.sub(r"[\*`_#]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _section(lines: list[str], start: str, ends: tuple[str, ...]) -> list[str]:
    """Lines of one markdown section (between heading ``start`` and the first
    heading in ``ends``); sub-headings (``###``) never terminate it."""
    out: list[str] = []
    started = False
    for line in lines:
        if not started:
            if line.lstrip().startswith(start):
                started = True
            continue
        if any(line.lstrip().startswith(e) for e in ends):
            break
        out.append(line)
    return out


def _pipe_rows(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells):
            continue
        rows.append(cells)
    return rows


def _norm_code(code: str) -> str:
    return re.sub(r"\D", "", code)


def _first_code(cell: str) -> str | None:
    m = re.search(r"\b(\d{4}(?:\.\d{2})?)\b", strip_markdown(cell))
    return _norm_code(m.group(1)) if m else None


def _eight_digit_codes(cell: str) -> list[str]:
    """All ITC-HS 8-digit codes in a cell ('5208 52 10' or '5310 10 91/92')."""
    codes: list[str] = []
    for m in re.finditer(r"\b(\d{4})\s+(\d{2})\s+(\d{2}(?:/\d{2})?)\b", strip_markdown(cell)):
        for part in m.group(3).split("/"):
            codes.append(f"{m.group(1)}{m.group(2)}{part}")
    return codes


# --- categories ----------------------------------------------------------------


def _parse_hs_rows(lines: list[str], sec1: list[str]) -> list[dict]:
    """hs_codes rows from the doc's §1: the prose ``6-digit HS:`` line (scarf
    doc shape) plus every table row with a code column.  Confidence mapped
    from the 🟢🟡🔴⚠️ legend; codes with ``x`` placeholders never match."""
    rows: list[dict] = []
    seen: set[tuple[str, str | None]] = set()

    def add(hs6: str, itc8: str | None, desc: str, conf: str) -> None:
        key = (hs6, itc8)
        if key in seen:
            return
        seen.add(key)
        rows.append({"hs6": hs6, "itc_hs_8": itc8, "description": desc, "confidence": conf})

    for line in lines:
        m = re.match(
            r"^\s*#+\s*6-digit HS[^:\n]*:\s*\*\*(\d{4}(?:\.\d{2})?)\*\*\s*[—–-]\s*(.+)$",
            line,
        )
        if m:
            add(_norm_code(m.group(1)), None, _clean(m.group(2)),
                _emoji_conf(m.group(2)) or "high")

    for cells in _pipe_rows(sec1):
        joined = " ".join(cells)
        if "out of scope" in joined.lower():
            continue  # e.g. jewellery 7113/7114 row — explicitly out of scope
        first = strip_markdown(cells[0]) if cells else ""
        is8 = bool(re.match(r"^\s*\d{4}\s+\d{2}\s+\d{2}", first))
        if is8:
            codes = _eight_digit_codes(first)
            desc = _clean(cells[1]) if len(cells) > 1 else ""
        else:
            hs6 = _first_code(cells[0]) if cells else None
            if not hs6:
                continue
            codes = []
            for cell in cells:
                codes += _eight_digit_codes(cell)
            desc = _clean(cells[1]) if len(cells) > 1 else ""
            if not desc:
                desc = f"HS heading {hs6}"
        conf = _emoji_conf(joined) or _word_conf(joined) or "moderate"
        for code in codes:
            add(code[:6], code, desc, conf)
        if not is8:
            add(hs6, None, desc, conf)  # type: ignore[arg-type]
    return rows


def _parse_certs(sec4: list[str]) -> list[dict]:
    """Certifications from §4.  Shape A docs carry a ``Need | Required? |
    Detail`` table; shape B docs use numbered sub-sections — fall back to
    (heading, first-sentence) pairs."""
    certs: list[dict] = []
    table = _pipe_rows(sec4)
    if table and "need" in " ".join(table[0]).lower():
        for cells in table[1:]:
            if len(cells) >= 3:
                certs.append({"need": cells[0], "required": cells[1], "detail": cells[2]})
        return certs
    for i, line in enumerate(sec4):
        m = re.match(r"^#{3,5}\s+(.+)$", line)
        if not m:
            continue
        detail = ""
        for ln in sec4[i + 1:]:
            s = ln.strip()
            if s and not s.startswith("|") and not s.startswith("#"):
                detail = _clean(s.lstrip("- "))[:240]
                break
        certs.append({"need": _clean(m.group(1)), "required": "", "detail": detail})
    return certs


def _parse_lane_fit(sec5: list[str]) -> dict:
    """Lane fit from §5: typical weight / weight profile, the per-destination
    ITPS-vs-EMS verdict table (shape A docs), EMS fallback note."""
    fit: dict = {}
    text = "\n".join(sec5)
    m = re.search(r"Typical parcel weight:\s*(.*?)(?:\n\s*\n|\Z)", text, re.DOTALL)
    if m:
        fit["typical_weight"] = _clean(m.group(1))
    m = re.search(r"Weight profile:\s*([^\n]*)", text)
    if m:
        fit["weight_profile"] = _clean(m.group(1))
    m = re.search(r"EMS fallback:\s*([^\n]*)", text)
    if m:
        fit["ems_fallback"] = _clean(m.group(1))
    verdicts: dict[str, str] = {}
    for cells in _pipe_rows(sec5):
        if not cells:
            continue
        market = re.sub(r"[\*`]", "", cells[0]).strip()
        if market in _MARKET_ISO2 and "ITPS" in cells[-1] or "EMS" in cells[-1]:
            verdicts[market] = _clean(cells[-1])
    if verdicts:
        fit["verdicts"] = verdicts
    return fit


def _doc_source_url(lines: list[str]) -> str:
    idx = next((i for i, l in enumerate(lines) if l.lstrip().startswith("## 6")), None)
    if idx is None:
        idx = max(0, len(lines) - 40)
    for line in lines[idx:]:
        m = re.search(r"https?://\S+", line)
        if m:
            return m.group(0).rstrip(".,;)")
    raise ValueError("no source URL found in category doc")


_S301_RE = re.compile(r"(?:Section 301|S\.?\s?301|S301)")
_RATE_RE = re.compile(r"(\d+(?:\.\d+)?)%")


def _nearest_conf(cell: str, pos: int, default: str) -> str:
    best, best_d = default, 10**9
    for emoji, conf in EMOJI_CONF.items():
        idx = cell.find(emoji)
        while idx != -1:
            if abs(idx - pos) < best_d:
                best_d, best = abs(idx - pos), conf
            idx = cell.find(emoji, idx + 1)
    return best


def _parse_market_rates(
    market: str, duty: str, tax: str, hs6_default: str
) -> list[dict]:
    """country_rates rows from one §3 market cell (USA/UK/UAE/Australia):
    MFN + S301 (US) from the duty cell, VAT/GST from the tax cell, and the
    duty-only de-minimis threshold in minor units."""
    iso2 = _MARKET_ISO2[market]
    currency = _MARKET_CURRENCY[iso2]
    rates: list[dict] = []

    def add(
        rate_type: str,
        rate_pct: float | None = None,
        threshold_minor: int | None = None,
        basis: str | None = None,
        hs6: str | None = None,
        conf: str = "moderate",
        cell: str | None = None,
        pos: int = 0,
    ) -> None:
        rates.append({
            "country_iso2": iso2,
            "hs6": hs6,
            "rate_type": rate_type,
            "rate_pct": rate_pct,
            "threshold_minor": threshold_minor,
            "currency": currency,
            "basis": basis,
            "confidence": _nearest_conf(cell, pos, conf) if cell is not None else conf,
        })

    # Section 301 (US only, 24-Jul-2026 net-of-MFN — every §3 US cell carries it)
    for m in _S301_RE.finditer(duty):
        rm = _RATE_RE.search(duty[m.end():m.end() + 30])
        if rm:
            add("S301", float(rm.group(1)), basis="netofmfn", conf="unverified",
                cell=duty, pos=m.start())
            break
    # MFN: first % that is not S301/VAT/GST, not a specific duty (…/kg+10%) and
    # not a material threshold ("≥70% silk" is fibre content, not a duty rate)
    for m in _RATE_RE.finditer(duty):
        window = duty[max(0, m.start() - 40):m.end() + 15]
        if _S301_RE.search(window) or re.search(r"\bVAT\b|\bGST\b", window):
            continue
        if re.search(r"[≥≤<>]", duty[max(0, m.start() - 10):m.start()]):
            continue
        if re.search(r"kg", duty[max(0, m.start() - 12):m.start()]):
            continue  # column-2 style "2.2¢/kg+10%" — not an ad valorem MFN
        hs6 = hs6_default
        toks = re.findall(r"\d{4}(?:\.\d{2})?(?:\.\d{2})?", duty[max(0, m.start() - 80):m.start()])
        if toks:
            hs6 = _norm_code(toks[0])[:6]
        basis = _clean(duty[max(0, m.start() - 45):m.start()])
        add("MFN", float(m.group(1)), basis=basis or "MFN", hs6=hs6,
            cell=duty, pos=m.start())
        break
    else:
        if "free" in duty.lower():
            add("MFN", 0.0, basis="Free", hs6=hs6_default, cell=duty, pos=0)
    # VAT / GST from the tax cell
    for m in _RATE_RE.finditer(tax):
        window = tax[max(0, m.start() - 25):m.end() + 12]
        basis = _clean(tax[max(0, m.start() - 25):m.end() + 12])
        if re.search(r"\bVAT\b", window):
            add("VAT", float(m.group(1)), basis=basis or "VAT", cell=tax, pos=m.start())
            break
        if re.search(r"\bGST\b", window):
            add("GST", float(m.group(1)), basis=basis or "GST", cell=tax, pos=m.start())
            break
    # duty-only de-minimis thresholds (minor units: £/AED/AUD × 100)
    for sym, mult in (("£", 100), ("AED", 100), ("AUD", 100)):
        m = re.search(rf"{sym}\s*([\d,]+)", duty)
        if m:
            add("DE_MINIMIS", threshold_minor=int(m.group(1).replace(",", "")) * mult,
                basis="duty-only de minimis" if sym == "AED" else "duty-free threshold",
                cell=duty, pos=m.start())
    return rates


def _parse_category_doc(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    slug = path.parent.name
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    name = re.sub(r"^Category Doc\s*[—–-]\s*", "", m.group(1).strip()) if m else slug
    sec1 = _section(lines, "## 1", ("## 2",))
    sec2 = _section(lines, "## 2", ("## 3",))
    sec3 = _section(lines, "## 3", ("## 4",))
    sec4 = _section(lines, "## 4", ("## 5",))
    sec5 = _section(lines, "## 5", ("## 6",))
    m = re.search(r"\*\*(\d{4}(?:\.\d{2})?)\*\*", "\n".join(sec1))
    hs6_default = _norm_code(m.group(1)) if m else None
    tmpl = None
    m = re.search(r"Template[^\n]*\n\s*```[^\n]*\n(.*?)```", "\n".join(sec2), re.DOTALL)
    if m:
        tmpl = m.group(1).strip()
    url = _doc_source_url(lines)
    rates: list[dict] = []
    for cells in _pipe_rows(sec3):
        market = re.sub(r"[\*`]", "", cells[0]).strip() if cells else ""
        if market not in _MARKET_ISO2:
            continue
        duty = cells[1] if len(cells) > 1 else ""
        tax = cells[2] if len(cells) > 2 else ""
        rates += _parse_market_rates(market, duty, tax, hs6_default or "")
    return {
        "slug": slug,
        "name": name,
        "hs6_default": hs6_default,
        "pbe_desc_template": tmpl,
        "certifications": _parse_certs(sec4),
        "lane_fit": _parse_lane_fit(sec5),
        "source_url": url,
        "hs_rows": _parse_hs_rows(lines, sec1),
        "rates": rates,
    }


def _import_categories(session: object) -> tuple[int, int, int]:
    n_cat = n_hs = n_rates = 0
    docs = sorted(CATEGORY_DIR.glob("*/category-doc.md"))
    if len(docs) != 8:
        raise RuntimeError(f"category gate failed: {len(docs)} docs, expected 8")
    for doc in docs:
        data = _parse_category_doc(doc)
        cat = ProductCategory(
            slug=data["slug"],
            name=data["name"],
            hs6_default=data["hs6_default"],
            pbe_desc_template=data["pbe_desc_template"],
            certifications=data["certifications"] or None,
            lane_fit=data["lane_fit"] or None,
            source_url=data["source_url"],
            source_level="L2",
            confidence="high",
            is_estimate=False,
            effective_from=SNAPSHOT_DATE,
            verified_at=VERIFIED_AT,
        )
        session.add(cat)  # type: ignore[attr-defined]
        session.flush()  # type: ignore[attr-defined]  # product_cat FK
        for h in data["hs_rows"]:
            session.add(HsCode(  # type: ignore[attr-defined]
                hs6=h["hs6"], itc_hs_8=h["itc_hs_8"], hts_10=None,
                description=h["description"], product_cat=cat.id,
                source_url=data["source_url"], source_level="L2",
                confidence=h["confidence"], is_estimate=False,
                effective_from=SNAPSHOT_DATE, verified_at=VERIFIED_AT,
            ))
        for r in data["rates"]:
            session.add(CountryRate(  # type: ignore[attr-defined]
                country_iso2=r["country_iso2"], hs6=r["hs6"], rate_type=r["rate_type"],
                rate_pct=r["rate_pct"], amount_minor=None, threshold_minor=r["threshold_minor"],
                currency=r["currency"], basis=r["basis"],
                source_url=data["source_url"], source_level="L2",
                confidence=r["confidence"], is_estimate=False,
                effective_from=SNAPSHOT_DATE, verified_at=VERIFIED_AT,
            ))
        n_cat += 1
        n_hs += len(data["hs_rows"])
        n_rates += len(data["rates"])
    return n_cat, n_hs, n_rates


# --- states --------------------------------------------------------------------

STATE_TAX_SOURCE = "https://taxfoundation.org/data/all/state/2026-sales-tax-rates-midyear/"


def _parse_states() -> list[dict]:
    """51-row master table ONLY (state-sales-tax-table.md lines 22–74, the
    "## A. The master table").  Sections B–E are reference prose and are never
    parsed as rows — the row-count gate (51) catches any bleed-through."""
    lines = STATE_TAX_FILE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().startswith("| # | State |"))
    cells_rows: list[list[str]] = []
    for line in lines[start + 1:]:
        s = line.strip()
        if not s.startswith("|"):
            break
        cells = [strip_markdown(c).strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells):
            continue
        cells_rows.append(cells)
    if len(cells_rows) != 51:
        raise RuntimeError(f"state master-table gate failed: {len(cells_rows)} rows, expected 51")

    out: list[dict] = []
    for cells in cells_rows:
        m = re.match(r"^(.+?)\s*\(([A-Z]{2})\)$", cells[1])
        if not m:
            raise ValueError(f"cannot parse state cell {cells[1]!r}")
        name, iso2 = m.group(1).strip(), m.group(2)
        rate = float(re.search(r"([\d.]+)%", cells[2]).group(1))
        if "None" in cells[3]:
            cmin = cmax = 0.0
        elif "–" in cells[3]:
            mm = re.search(r"([\d.]+)\s*–\s*([\d.]+)", cells[3])
            cmin, cmax = float(mm.group(1)), float(mm.group(2))
        else:
            cmin = cmax = float(re.search(r"([\d.]+)%", cells[3]).group(1))
        threshold = None
        if iso2 not in _NO_STATE_NEXUS:
            tm = re.search(r"\$([\d,]+)", cells[4])
            threshold = int(tm.group(1).replace(",", "")) if tm else None
        tx_test = bool(re.search(r"200 transactions|>100 transactions", cells[4]))
        notes = cells[5].strip()
        if iso2 == "KY":
            tx_test = False  # 200-tx test repealed 01-Aug-2026 (17 remain active)
            notes += " 200-tx test repealed 01-Aug-2026 (17 transaction-test states remain)."
        elif tx_test and "AND" in cells[4]:
            notes += " AND-test: both dollar and transaction tests required."
        out.append({
            "state_iso2": iso2, "state_name": name,
            "state_rate_pct": rate, "combined_min_pct": cmin, "combined_max_pct": cmax,
            "nexus_threshold_usd": threshold, "nexus_tx_test": tx_test, "notes": notes,
        })
    return out


def _import_states(session: object) -> int:
    rows = _parse_states()
    for r in rows:
        session.add(StateSalesTax(  # type: ignore[attr-defined]
            state_iso2=r["state_iso2"], state_name=r["state_name"],
            state_rate_pct=r["state_rate_pct"],
            combined_min_pct=r["combined_min_pct"], combined_max_pct=r["combined_max_pct"],
            nexus_threshold_usd=r["nexus_threshold_usd"], nexus_tx_test=r["nexus_tx_test"],
            notes=r["notes"],
            source_url=STATE_TAX_SOURCE, source_level="L2", confidence="high",
            is_estimate=False, effective_from=date(2026, 7, 1), verified_at=VERIFIED_AT,
        ))
    return len(rows)


# --- flags ---------------------------------------------------------------------
# Every flag is traceable to the pack (country duties-taxes files, lane docs,
# payment/incentive docs).  flag_value is a JSONB scalar or flat array —
# never an object wrapper (pinned by the verification gates).

_US_USTR = ("https://ustr.gov/sites/default/files/files/Press/Releases/2026/"
            "FLIP%20301%20Investigation%20Final%20Action%20FRN%207-23-26%20FINAL.pdf")
_US_DEMINIMIS = ("https://www.cbp.gov/sites/default/files/2025-08/"
                 "factsheet_suspension_of_duty-free_de_minimis_treatment.pdf")
_US_CBP_FAQ = "https://www.cbp.gov/trade/basic-import-export/e-commerce/faqs"
_US_USPS_FEE = "https://www.govinfo.gov/content/pkg/FR-2026-01-08/html/2026-00164.htm"
_UK_GOV_TAX = "https://www.gov.uk/goods-sent-from-abroad/tax-and-duty"
_UK_RM_FEE = "https://www.royalmail.com/receiving-mail/pay-a-fee"
_UK_CETA = ("https://www.gov.uk/government/news/"
            "historic-uk-india-free-trade-agreement-is-now-in-effect")
_AE_FTA = "https://tax.gov.ae"
_AE_EMX = "https://www.emx.ae/vat"
_AE_CUSTOMS = ("https://www.dubaicustoms.gov.ae/en/OpenData/Publications/"
               "Customer_Guide_Booklet_EN.pdf")
_AE_DEMINIMIS = "https://samvertex.com/blog/uae-customs-de-minimis-2026/"
_AE_CEPA = ("https://www.moet.gov.ae/documents/20121/1347101/"
            "Final+Agreement_UAE+India+CEPA.pdf")
_AE_WHO_PAYS = ("https://www.thenationalnews.com/business/money/vat-q-a-why-am-i-"
                "charged-tax-to-pick-up-a-parcel-from-the-post-office-1.730293")
_AU_ATO_LVIG = ("https://www.ato.gov.au/businesses-and-organisations/international-"
                "tax-for-business/gst-for-non-resident-businesses/"
                "gst-on-low-value-imported-goods")
_AU_ATO_IMPORT = ("https://www.ato.gov.au/businesses-and-organisations/gst-excise-"
                  "and-indirect-taxes/gst/in-detail/rules-for-specific-transactions/"
                  "international-transactions/gst-and-imported-goods")
_AU_ATO_GST = ("https://www.ato.gov.au/businesses-and-organisations/international-"
               "tax-for-business/gst-for-non-resident-businesses/how-australian-gst-works")
_AU_IPC = ("https://www.legislation.gov.au/C2004A00857/2016-07-01/2016-07-01/text/"
           "original/epub/OEBPS/document_1/document_1.html")
_AU_ECTA = ("https://www.dfat.gov.au/trade/agreements/in-force/australia-india-ecta/"
            "australia-india-ecta-official-text")
_AU_COO = "https://coo.dgft.gov.in/"
_AU_DAFF = "https://www.agriculture.gov.au/biosecurity-trade/import/goods/timber"
_AU_BICON = "https://bicon.agriculture.gov.au/"
_ITPS_OM = "https://www.potoolsblog.in/2026/01/amendment-of-international-tracked.html"
_ITPS_SOP = "https://www.potoolsblog.in/2025/04/standard-operating-procedure-sop-for.html"
_ITPS_TRANSIT = "https://trackmyspeedpost.com/delivery-time-by-service"
_EMS_INDIA_POST = "https://indiapost.org/international-speed-post-ems"
_EMS_DOP = "https://test.cept.gov.in/enterpriseportal/mails/international-mail/international-speedpost"
_EMS_SCHEDULE_IV = "https://www.speedpost.report/2024/12/schedule-iv.html"
_EMS_CLICKPOST = "https://www.clickpost.ai/blog/international-speed-post"
_EMS_CONFLICTS = "https://www.clickpost.ai/blog/india-post-courier-charges"
_CN22_POSTALSTUDY = "https://www.postalstudy.in/2022/03/instructions-on-kyc-for-foreign.html"
_PBE_NTF104 = ("https://taxguru.in/custom-duty/postal-export-electronic-declaration-"
               "processing-regulations-2022-implementation-pbe-automated-system.html")
_RAZORPAY = "https://razorpay.com/pricing/"
_WISE_HELP = ("https://wise.com/help/articles/71lNXW0Ls3gEFhUH8PtodV/"
              "receiving-payments-for-indian-businesses")
_WISE_REVIEW = ("https://www.infinityapp.in/blog/"
                "wise-(transferwise)-india-features-benefits-and-alternatives")
_PAYPAL_FEES = "https://www.paypal.com/in/business/paypal-business-fees"
_ETSY_FEES = "https://www.karboncard.com/blog/etsy-payouts-india-fees-conversion"
_FEMA_9MO = ("https://taxguru.in/rbi/foreign-exchange-management-export-goods-services-"
             "first-amendment-regulations-2026.html")
_FEMA_15MO = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62478"
_RODTEP_SCRIP = ("https://www.icegate.gov.in/guidelines/advisory-e-scrip-avail-export-"
                 "incentive-schemes-rosctl-rodtep")
_RODTEP_DISCOUNT = "https://allfrontierglobal.com/gdocs/doc106-faq-rodtep-scheme/"
_LABELS_SRC = "https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2055743"

# (flag_key, value, source_url, source_level, confidence, is_estimate, effective_from)
FLAG_SPECS: list[tuple[str, object, str, str, str, bool, date | None]] = [
    # --- US (duties-taxes.md §1/§7) ---
    ("us.usps_clearance_fee_minor", 935, _US_USPS_FEE, "L1", "high", False, None),
    ("us.deminimis.suspended", True, _US_DEMINIMIS, "L1", "high", False, date(2025, 8, 29)),
    ("us.s301.rate_pct", 10, _US_USTR, "L1", "high", False, date(2026, 7, 24)),
    ("us.s301.basis", "netofmfn", _US_USTR, "L1", "high", False, date(2026, 7, 24)),
    ("us.entry_formal_threshold_minor", 250000, _US_CBP_FAQ, "L1", "high", False, None),
    ("us.duty_basis", "S301_10_pct_netofmfn", _US_USTR, "L1", "high", False, date(2026, 7, 24)),
    ("us.mpf.postal", "exempt_itps_liable_ems", _US_CBP_FAQ, "L1", "high", False, None),
    # --- UK (duties-taxes.md §1–§6) ---
    ("uk.duty_freethreshold_minor", 13500, _UK_GOV_TAX, "L1", "high", False, None),
    ("uk.vat_pct", 20, _UK_GOV_TAX, "L1", "high", False, None),
    ("uk.royalmail_handling_fee_minor", 800, _UK_RM_FEE, "L1", "high", False, None),
    ("uk.parcelforce_handling_fee_minor", 1200, _UK_RM_FEE, "L1", "high", False, None),
    ("uk.ceta_in_force", True, _UK_CETA, "L1", "high", False, date(2026, 7, 15)),
    ("uk.gift_vat_threshold_minor", 3900, _UK_GOV_TAX, "L1", "high", False, None),
    ("uk.gift_reduced_duty_rate_pct", 2.5, _UK_GOV_TAX, "L1", "high", False, None),
    # --- UAE (duties-taxes.md §1) ---
    ("uae.vat_pct", 5, _AE_FTA, "L1", "high", False, None),
    ("uae.duty_rate_pct", 5, _AE_CUSTOMS, "L1", "high", False, None),
    ("uae.deminimis_duty_only_aed", 1000, _AE_DEMINIMIS, "L3", "high", False, None),
    ("uae.default_value_aed", 1000, _AE_EMX, "L1", "high", False, None),
    ("uae.cepa_preferential", True, _AE_CEPA, "L1", "high", False, None),
    ("uae.who_pays", "recipient_at_pickup", _AE_WHO_PAYS, "L2", "high", False, None),
    # --- Australia (duties-taxes.md §5) ---
    ("au.gst_pct", 10, _AU_ATO_LVIG, "L1", "high", False, None),
    ("au.deminimis_aud", 1000, _AU_ATO_IMPORT, "L1", "high", False, None),
    ("au.lvig_vendor_collection", True, _AU_ATO_LVIG, "L1", "high", False, date(2018, 7, 1)),
    ("au.gst_registration_threshold_aud", 75000, _AU_ATO_GST, "L1", "high", False, None),
    ("au.ipc_fee_1k_10k_minor", 5000, _AU_IPC, "L1", "moderate", False, None),
    ("au.ipc_fee_10k_plus_minor", 15200, _AU_IPC, "L1", "moderate", False, None),
    ("au.ecta_preferential", True, _AU_ECTA, "L1", "high", False, date(2022, 12, 29)),
    ("au.ecta_coo_required", True, _AU_COO, "L1", "high", False, None),
    ("au.biosecurity_wood", "required_bicon", _AU_DAFF, "L1", "moderate", False, None),
    ("au.biosecurity_jute", "required_bicon", _AU_BICON, "L1", "moderate", False, None),
    # --- ITPS (itps-lane.md §4/§5, S.O. 659(E) via potoolsblog mirror) ---
    ("itps.portal_discount_pct", 2, _ITPS_SOP, "L3", "moderate", False, None),
    ("itps.us.first50_minor", 40000, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.us.addl50_minor", 3500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uk.first50_minor", 20000, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uk.addl50_minor", 2500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uae.first50_minor", 18500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.uae.addl50_minor", 1500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.au.first50_minor", 39500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.au.addl50_minor", 4500, _ITPS_OM, "L2", "high", False, date(2026, 2, 6)),
    ("itps.us.cap_kg", 5, _ITPS_OM, "L2", "high", False, date(2026, 1, 1)),  # O10 resolved
    ("itps.au.cap_kg", 2, _ITPS_OM, "L1", "high", False, None),
    ("itps.canada.cap_kg", 2, _ITPS_OM, "L1", "high", False, None),
    # --- EMS (ems-lane.md §4/§9/§11; rates L5 — Schedule I never public, C11) ---
    ("ems.portal_discount_pct", 1, _ITPS_SOP, "L3", "moderate", False, None),
    ("ems.delay_comp_pct", 5, _EMS_DOP, "L1", "high", False, None),
    ("ems.us.first250_minor", 86500, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.us.addl250_minor", 10000, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.uk.first250_minor", 86500, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.uk.addl250_minor", 10000, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.au.first250_minor", 63000, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.au.addl250_minor", 15500, _EMS_INDIA_POST, "L5", "low", True, None),
    ("ems.insurance_first_200_minor", 1000, _EMS_SCHEDULE_IV, "L1", "high", False, None),
    ("ems.insurance_addl_100_minor", 600, _EMS_SCHEDULE_IV, "L1", "high", False, None),
    # --- forms / volumetric / KYC ---
    ("cn22.sdr_max", 300, _CN22_POSTALSTUDY, "L3", "high", False, None),
    ("kyc.declared_value_minor", 2500000, _EMS_CLICKPOST, "L5", "low", True, None),
    ("volumetric.divisors", [4000, 5000, 6000], _EMS_CONFLICTS, "L5", "unverified", True, None),
    ("pbe.declaration_clusters", 6, _PBE_NTF104, "L1", "moderate", False, None),
    ("pbe.ecomm_columns", 5, _PBE_NTF104, "L1", "high", False, None),
    # --- transit (L5 ranges only — never points) ---
    ("itps.transit.us_days", [18, 28], _ITPS_TRANSIT, "L5", "low", True, None),
    ("itps.transit.uk_days", [16, 25], _ITPS_TRANSIT, "L5", "low", True, None),
    ("itps.transit.uae_days", [14, 21], _ITPS_TRANSIT, "L5", "low", True, None),
    ("itps.transit.au_days", [18, 28], _ITPS_TRANSIT, "L5", "low", True, None),
    ("ems.transit.us_days", [5, 14], _EMS_CLICKPOST, "L5", "low", True, None),
    ("ems.transit.uk_days", [4, 14], _EMS_CLICKPOST, "L5", "low", True, None),
    ("ems.transit.uae_days", [3, 8], _EMS_CLICKPOST, "L5", "low", True, None),
    ("ems.transit.au_days", [5, 14], _EMS_CLICKPOST, "L5", "low", True, None),
    # --- payment rails (vendor-published; ranges/estimates labelled) ---
    ("razorpay.intl_cards_fee_pct", 3, _RAZORPAY, "L3", "moderate", False, None),
    ("razorpay.bank_transfer_fee_pct", 1, _RAZORPAY, "L3", "moderate", False, None),
    ("wise.conversion_fee_range_pct", [1.6, 1.7], _WISE_REVIEW, "L4", "low", True, None),
    ("wise.efirc_fee_minor", 200, _WISE_HELP, "L3", "moderate", False, None),
    ("paypal.allin_fee_range_pct", [7, 8], _PAYPAL_FEES, "L3", "low", True, None),
    ("etsy.payoneer_total_fee_range_pct", [12, 15], _ETSY_FEES, "L4", "low", True, None),
    # --- FEMA / incentives ---
    ("fema.realisation_months", 9, _FEMA_9MO, "L2", "high", False, date(2026, 6, 5)),
    ("fema.relaxation_months", 15, _FEMA_15MO, "L1", "high", False, date(2026, 3, 31)),
    ("rodtep.not_cash", True, _RODTEP_SCRIP, "L1", "high", False, None),
    ("rodtep.scrip_discount_range_pct", [3, 8], _RODTEP_DISCOUNT, "L5", "low", True, None),
    # --- bilingual UI labels (pinned by todo 11's preview gate) ---
    ("labels.estimate.hi", "अनुमानित", _LABELS_SRC, "L2", "high", False, None),
    ("labels.estimate.kn", "ಅಂದಾಜು", _LABELS_SRC, "L2", "high", False, None),
    ("labels.estimate.en", "estimate", _LABELS_SRC, "L2", "high", False, None),
    ("labels.please.hi", "कृपया", _LABELS_SRC, "L2", "high", False, None),
    ("labels.please.kn", "ದಯವಿಟ್ಟು", _LABELS_SRC, "L2", "high", False, None),
    ("labels.source.hi", "स्रोत", _LABELS_SRC, "L2", "high", False, None),
    ("labels.source.kn", "ಮೂಲ", _LABELS_SRC, "L2", "high", False, None),
    ("labels.source.en", "source", _LABELS_SRC, "L2", "high", False, None),
    ("labels.confirm.hi", "कृपया पुष्टि करें", _LABELS_SRC, "L2", "high", False, None),
    ("labels.confirm.kn", "ದಯವಿಟ್ಟು ದೃಢೀಕರಿಸಿ", _LABELS_SRC, "L2", "high", False, None),
]


def _import_flags(session: object) -> tuple[int, int]:
    if len(FLAG_SPECS) < 40:
        raise RuntimeError(f"config-flag gate failed: pack yields {len(FLAG_SPECS)} flags (< 40)")
    for key, value, url, level, conf, est, eff in FLAG_SPECS:
        session.add(ConfigFlag(  # type: ignore[attr-defined]
            flag_key=key, flag_value=value,
            source_url=url, source_level=level, confidence=conf, is_estimate=est,
            effective_from=eff or SNAPSHOT_DATE, verified_at=VERIFIED_AT,
        ))
    n_labels = sum(1 for spec in FLAG_SPECS if spec[0].startswith("labels."))
    return len(FLAG_SPECS), n_labels


# --- pbe -----------------------------------------------------------------------
#
# Field schemas for Forms PBE-III and PBE-IV as SUBSTITUTED by CBIC
# Notification No. 07/2026-Customs (N.T.), 15-Jan-2026 — the primary document
# is data/06-legal-sources/notification-07-2026-customs.{pdf,txt}.  The
# sections, column labels and declaration wording below are VERBATIM from that
# Notification (the .txt is an OCR render: "poslal"→"postal",
# "publiested"→"published", "l5"→"15", etc. were cleaned, but the column
# labels are kept in their official form).
#
# Only fields with a REAL data source in DocumentData are marked required:
# consignee_details, product_description, cth, quantity_unit, gross_weight,
# net_weight (the six extraction-contract fields) and assessable_value
# (value_minor).  Everything else renders "—" — the form is honest about what
# the pipeline does not know (the exporter fills those at submission).

PBE_SOURCE_LEVEL = {"high": "L1", "moderate": "L2"}
_PBE_NTF07 = "data/06-legal-sources/notification-07-2026-customs.pdf"


def _pbe_rows() -> list[PbeFieldSchema]:
    """Official PBE-III/IV field schemas (Notification No. 07/2026-Customs)."""
    rows: list[PbeFieldSchema] = []

    def add(
        form: str, section: str, key: str, label: str, required: bool,
        vtype: str, validation: str, options: dict | None = None, conf: str = "high",
    ) -> None:
        rows.append(PbeFieldSchema(
            form_type=form, section=section, field_key=key, label=label,
            required=required, value_type=vtype, validation=validation, options=options,
            source_url=_PBE_NTF07, source_level=PBE_SOURCE_LEVEL[conf],
            confidence=conf, is_estimate=False,
            effective_from=SNAPSHOT_DATE, verified_at=VERIFIED_AT,
        ))

    # --- Header (the official 9-field header block) ---------------------------
    header = [
        ("boe_no", "Bill of Export No. and date", False, "auto",
         "System-generated on submission (Article ID + PBE number pop-up)"),
        ("fpo_code", "Foreign Post Office code", False, "string",
         "Code of the Board-appointed Foreign Post Office mapped to the booking post office"),
        ("exporter_name", "Name of Exporter", False, "string",
         "Auto-populated from DGFT IEC validation (name, address, city, pincode, PAN)"),
        ("exporter_address", "Address of Exporter", False, "string",
         "Auto-populated from DGFT IEC validation (name, address, city, pincode, PAN)"),
        ("iec", "IEC", False, "string",
         "10-char alphanumeric, validated live against DGFT; booking disabled if suspended"),
        ("state_code", "State Code", False, "string", "Exporter's state code"),
        ("gstin_or_as_applicable", "GSTIN or as applicable", False, "string",
         "15-char GSTIN; not uniformly mandatory — booking gates on ≥1 of IEC/GSTIN"),
        ("ad_code", "AD code (if Applicable)", False, "string",
         "14-char AD code; required on ICEGATE for electronic claims"),
        ("customs_broker_license_no", "Customs Broker License No.", False, "string",
         "Details of authorized agent — Customs Broker License No. (CBLR 2018)"),
        ("agent_name_address", "Name and address", False, "string",
         "Details of authorized agent — name and address"),
    ]
    # --- Details of parcel (columns common to both forms) ---------------------
    parcel = [
        ("si_no", "SI. No", False, "number", "Line number of the item in the consignment"),
        ("consignee_details", "Name and Address", True, "string",
         "Consignee name and address (postcode validated; in-portal lookup)"),
        ("destination_country", "Country of destination", False, "string",
         "ISO2 country code of destination"),
        ("product_description", "Description", True, "string",
         "No vague descriptions — description↔HS mismatch is a documented error"),
        ("cth", "CTH", True, "string", "Customs Tariff Heading (HS/CTH code per item)"),
        ("quantity_unit", "Quantity / Unit (pieces, liters, kgs., meters, Pairs etc.)",
         True, "number", "Quantity with unit — pieces, liters, kgs., meters, Pairs etc."),
        ("invoice_no_date", "Invoice No. and date", False, "string",
         "Invoice number and date of the parcel item"),
        ("gross_weight", "Gross", True, "number", "Weight of parcel with packaging"),
        ("net_weight", "Net", True, "number", "Product weight (net of packaging)"),
    ]
    # PBE-III only — E-commerce particulars (5 official columns).
    ecomm = [
        ("ecomm_operator_gstin", "GSTIN of E-commerce operator", False, "string",
         "GSTIN of the marketplace operator — not the artisan's own"),
        ("ecomm_url", "URL (Name) of website", False, "url",
         "Marketplace/website URL where the order was placed"),
        ("ecomm_payment_txn_id", "Payment transaction ID", False, "string",
         "Electronic payment reference — the order→payment binding key"),
        ("ecomm_sku_no", "SKU No.", False, "string",
         "Marketplace SKU / product identifier"),
        ("ecomm_postal_tracking", "Postal Tracking Number", False, "string",
         "The article's S10 postal tracking number once generated"),
    ]
    # PBE-IV only — Postal Tracking number (PBE-IV = other postal exports).
    postal_tracking = [
        ("postal_tracking_number", "Postal Tracking number", False, "string",
         "The article's S10 postal tracking number once generated"),
    ]
    # --- Assessable value under section 14 (of the Customs Act, 1962) ---------
    assessable = [
        ("fob_value", "FOB", False, "money", "FOB value of the goods"),
        ("currency", "Currency", False, "string",
         "Currency of the invoice (INR when the declared value is in INR)"),
        ("exchange_rate", "Exchange rate", False, "number",
         "CBIC-notified exchange rate for the currency"),
        ("amount_inr", "Amount in INR", False, "money",
         "Amount in INR after conversion at the exchange rate"),
        ("hs_code", "H.S code", False, "string", "H.S code of the item"),
        ("tax_invoice_no_date", "Invoice no. and date", False, "string",
         "Details of Tax Invoice or commercial invoice — invoice no. and date"),
        ("si_no_item", "SI. No of item in invoice", False, "number",
         "Details of Tax Invoice or commercial invoice — line number in the invoice"),
        ("assessable_value", "Value", True, "money",
         "Value of the item — assessable value under section 14 of the Customs Act, 1962"),
    ]
    # --- Details of Duty/Tax --------------------------------------------------
    duty = [
        ("export_duty_rate", "Export duty Rate", False, "number", "Export duty rate (%)"),
        ("export_duty_amount", "Export duty Amount", False, "money", "Export duty amount"),
        ("cess_rate", "Cess Rate", False, "number", "Cess rate (%)"),
        ("cess_amount", "Cess Amount", False, "money", "Cess amount"),
        ("igst_rate", "IGST (if applicable) Rate", False, "number", "IGST rate (%)"),
        ("igst_amount", "IGST (if applicable) Amount", False, "money", "IGST amount"),
        ("comp_cess_rate", "Compensation cess (if applicable) Rate", False, "number",
         "Compensation cess rate (%)"),
        ("comp_cess_amount", "Compensation cess (if applicable) Amount", False, "money",
         "Compensation cess amount"),
        ("lut_bond", "LUT/bond details (if applicable)", False, "string",
         "Letter of Undertaking / bond details"),
        ("gst_duties", "Duties", False, "money", "GST details — duties"),
        ("gst_cess", "Cess", False, "money", "GST details — cess"),
        ("total_duty_tax", "Total", False, "money", "Total duty/tax for the parcel"),
    ]
    # --- Additional details of parcel (duty drawback / export scheme) ---------
    additions = [
        ("invoice_no", "Invoice No.", False, "string", "Invoice number of the item", None),
        ("item_serial_no", "Item Serial No. in Invoice", False, "number",
         "Line number of the item in the invoice", None),
        ("ritc_itc_hs", "RITC code/ITC-HS code", False, "string",
         "8-digit ITC-HS code the claim keys on", None),
        ("dbk_serial_no", "DBK serial No.", False, "string",
         "Duty-Drawback schedule serial number (if claiming drawback)", None),
        ("drawback_quantity", "Drawback quantity", False, "number",
         "Quantity on which drawback is claimed", None),
        ("igst_payment_status", "IGST payment status (Yes/No)", False, "boolean",
         "Yes/No — governs IGST-refund vs drawback mutual exclusivity",
         {"values": ["Yes", "No"]}),
        ("end_use", "End use of item", False, "string", "End-use description", None),
        ("scheme_code", "Scheme code", False, "string",
         "The export scheme chosen", {"values": ["drawback", "rodtep", "rosctl"]}),
        ("add_freight", "Add Freight (₹/Y/N)", False, "string",
         "Whether freight is added to the assessable value", {"values": ["Y", "N"]}),
        ("nature_of_contract", "Nature of contract (CIF/CF/C&F/FOB)", False, "string",
         "Nature of the sale contract", {"values": ["CIF", "CF", "C&F", "FOB"]}),
    ]
    # --- Declarations (verbatim wording from Ntf 07/2026, Yes/No as applicable)
    zero_rate_decl = (
        "1. I/We declare that we intend to zero rate our exports under section 16 of "
        "Integrated Goods and Services Tax Act, 2017."
    )
    exemption_decl = (
        "2. I/We declare that the goods are exempted under Central Goods and Services "
        "Tax Act/State Goods and Services Tax Act/Union Territory Goods and Services "
        "Tax/Integrated Goods and Services Tax Act, 2017."
    )
    drawback_decl = (
        "3. I/We declare that I/we intend to claim Drawback under Sec. 75 of Customs "
        "Act, 1962 and Customs and Central Excise Duties Drawback Rules, 2011.\n"
        "(a) I/We declare that no input tax credit of the central goods and Services Tax or of the "
        "integrated Goods and Services Tax has been availed for any of the inputs or input services used "
        "in the manufacture of the export goods.\n"
        "(b) I/We declare that no refund of Integrated Goods and Service Tax paid on export goods shall "
        "be claimed.\n"
        "(c) I/We declare that CENVAT credit on the inputs or input services used in the manufacture of "
        "the export goods, has not been carried forward in terms of the Central Goods and Service Tax Act, "
        "2017.\n"
        "(d) I/We certify that I/We have complied with the conditions laid down in the said Rules and the "
        "conditions subject to which Drawback Rates are applicable."
    )
    rodtep_decl = (
        "4. I/We declare that I/we intend to claim RoDTEP (Remission of Duties and Taxes on Exported "
        "Products),\n"
        "(a) I/We undertake to abide by the provisions, including conditions, restrictions, exclusions "
        "and time-limits as provided under RoDTEP scheme, and relevant notifications, regulations, etc.\n"
        "(b) Any claim made in this Postal Bill of Export is not with respect to any duties or taxes or "
        "levies which are exempted or remitted or credited under any other mechanism outside RoDTEP.\n"
        "(c) I/We undertake to preserve and make available relevant documents relating to the exported "
        "goods for the purposes of audit in the manner and for the time period prescribed in the Customs "
        "Audit Regulations, 2018."
    )
    rosctl_decl = (
        "5. I/We declare that I/we intend to claim RoSCTL (Rebate of State and Central Taxes and "
        "Levies),\n"
        "(a) I/We undertake to abide by the provisions, including conditions, restrictions, exclusions "
        "and time-limits as provided under RoSCTL scheme, and relevant notifications, regulations, etc.\n"
        "(b) Any claim made in this Postal Bill of Export is not with respect to any duties or taxes or "
        "levies which are exempted or remitted or credited under any other mechanism outside RoSCTL.\n"
        "(c) I/We undertake to preserve and make available relevant documents relating to the exported "
        "goods for the purposes of audit in the manner and for the time period prescribed in the Customs "
        "Audit Regulations, 2018."
    )
    fema_decl = (
        "6. I/We undertake to abide by the provisions of Foreign Exchange Management Act, 1999, as "
        "amended from time to time, including realisation or repatriation of foreign exchange to or from "
        "India."
    )
    decls = [
        ("decl.zero_rating_s16_igst", zero_rate_decl,
         "Declaration that the supply is a zero-rated export (s.16 IGST)"),
        ("decl.exemption", exemption_decl,
         "Exemption declaration (CGST/SGST/UTGST/IGST)"),
        ("decl.drawback", drawback_decl,
         "Drawback declaration — 4 sub-declarations (a)–(d), verbatim wording"),
        ("decl.rodtep", rodtep_decl,
         "RoDTEP declaration — 3 sub-declarations (a)–(c)"),
        ("decl.rosctl", rosctl_decl,
         "RoSCTL declaration — 3 sub-declarations (a)–(c)"),
        ("decl.fema_undertaking", fema_decl,
         "FEMA 1999 undertaking — realisation/repatriation of export proceeds"),
    ]

    for form in ("PBE_III", "PBE_IV"):
        for key, label, req, vtype, val in header:
            add(form, "Header", key, label, req, vtype, val)
        for key, label, req, vtype, val in parcel:
            add(form, "Details of parcel", key, label, req, vtype, val)
        if form == "PBE_III":
            for key, label, req, vtype, val in ecomm:
                add(form, "Details of parcel", key, label, req, vtype, val)
        else:
            for key, label, req, vtype, val in postal_tracking:
                add(form, "Details of parcel", key, label, req, vtype, val)
        for key, label, req, vtype, val in assessable:
            add(form, "Assessable value", key, label, req, vtype, val)
        for key, label, req, vtype, val in duty:
            add(form, "Details of Duty/Tax", key, label, req, vtype, val)
        for key, label, req, vtype, val, options in additions:
            add(form, "Additional details of parcel", key, label, req, vtype, val, options)
        for key, label, val in decls:
            add(form, "Declarations", key, label, False, "boolean", val,
                {"values": ["Yes", "No", "NA"]})
    return rows


def _import_pbe(session: object) -> tuple[int, int]:
    rows = _pbe_rows()
    if len(rows) < 30:
        raise RuntimeError(f"PBE schema gate failed: {len(rows)} rows (< 30)")
    n3 = sum(1 for r in rows if r.form_type == "PBE_III")
    for r in rows:
        session.add(r)  # type: ignore[attr-defined]
    return n3, len(rows) - n3


# --- combined todo-7 runner ----------------------------------------------------


def import_configs(*, categories: bool, states: bool, flags: bool, pbe: bool) -> str:
    """Seed the six todo-7 config tables in ONE transaction — idempotent."""
    with SessionLocal.begin() as session:
        session.execute(CONFIG_TRUNCATE)
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
    parser.add_argument(
        "--all",
        action="store_true",
        help="serial re-seed of every table: lanes (todo 6), then the six "
        "config tables (todo 7) — idempotent, runs ALONE",
    )
    args = parser.parse_args(argv)

    todo7 = [flag for flag in ("categories", "states", "flags", "pbe") if getattr(args, flag)]

    if args.all:
        if args.lanes or todo7:
            parser.error("--all must run alone (it re-seeds every table serially)")
        try:
            itps, ems = import_lanes()
            print(f"imported {itps} ITPS + {ems} EMS = {itps + ems} lanes")
            print(import_configs(categories=True, states=True, flags=True, pbe=True))
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
        parser.error("no subcommand given — use --categories/--states/--flags/--pbe (or --lanes)")

    try:
        print(import_configs(
            categories="categories" in todo7,
            states="states" in todo7,
            flags="flags" in todo7,
            pbe="pbe" in todo7,
        ))
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
