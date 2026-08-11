"""US state sales-tax seeds (todo 7) — the 51-row master table ONLY
(state-sales-tax-table.md §A); sections B-E are reference prose, never rows.
"""

from __future__ import annotations

import re
from datetime import date

from app.models import StateSalesTax
from app.parsers.markdown_tables import strip_markdown
from app.services.seed._common import DATA_DIR, VERIFIED_AT

STATE_TAX_FILE = DATA_DIR / "01-countries" / "USA" / "state-sales-tax-table.md"

_NO_STATE_NEXUS = {"OR", "NH", "MT", "DE", "AK"}  # no state-level sales-tax nexus


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
