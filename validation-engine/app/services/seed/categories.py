"""Product categories + hs_codes + country_rates seeds (todo 7) — parsed
from the category docs under data/03-product-categories.  Confidence maps
from the 🟢🟡🔴⚠️ legend; money is integer minor units.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.models import CountryRate, HsCode, ProductCategory
from app.parsers.markdown_tables import strip_markdown
from app.services.seed._common import DATA_DIR, SNAPSHOT_DATE, VERIFIED_AT

CATEGORY_DIR = DATA_DIR / "03-product-categories"

EMOJI_CONF = {"🟢": "high", "🟡": "moderate", "🔴": "low", "⚠️": "unverified"}
_EMOJI_RE = re.compile(r"[\u2600-\u27BF\u2B00-\u2BFF\U0001F000-\U0001FAFF\uFE0F]")
_MARKET_ISO2 = {"USA": "US", "UK": "GB", "UAE": "AE", "Australia": "AU"}
_MARKET_CURRENCY = {"US": "USD", "GB": "GBP", "AE": "AED", "AU": "AUD"}


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
