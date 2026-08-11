"""Country name → ISO-3166-1 alpha-2 mapping for the corpus country tables.

``to_iso2`` resolves a country name with a static alias map FIRST (corpus
spellings that pycountry cannot resolve exactly, plus deliberately pinned
names), then falls back to pycountry exact matching against ``name``,
``official_name`` and ``common_name``.

Any name that maps to nothing RAISES ``UnmappedCountryError`` — never
returns ``None``, never silently skips.  The 135/135 ITPS import gate and
the pytest alias pins depend on this strictness.
"""

from __future__ import annotations

import pycountry

# Static aliases, checked BEFORE pycountry so a wrong entry here fails both
# tests/test_iso2.py and the 135/135 import gate.  Covers corpus spellings
# pycountry cannot resolve exactly (accents, parenthesised notes, official
# names, older ISO spellings).
ALIASES: dict[str, str] = {
    "Cote d'Ivoire": "CI",  # pycountry: "Côte d'Ivoire" (accented)
    "Curacao": "CW",  # pycountry: "Curaçao" (accented)
    "Czechia": "CZ",  # pinned (pycountry also resolves it)
    "Eswatini": "SZ",  # pinned
    "Great Britain (UK)": "GB",  # pycountry: "United Kingdom"
    "Iran": "IR",  # pycountry: "Iran, Islamic Republic of"
    "Korea (Republic of)": "KR",  # pycountry: "Korea, Republic of"
    "Macao (China)": "MO",  # pycountry: "Macao"
    "Moldova": "MD",  # pycountry: "Moldova, Republic of"
    "Russian Federation": "RU",  # official name, pinned
    "Tanzania": "TZ",  # pycountry: "Tanzania, United Republic of"
    "Türkiye": "TR",  # pinned (pycountry also resolves it)
    "United Arab Emirates": "AE",  # pinned
    "United States of America": "US",  # official name
    "Vietnam": "VN",  # pycountry: "Viet Nam"
}


class UnmappedCountryError(ValueError):
    """Raised when ``to_iso2`` cannot map a country name to an ISO code."""


def _normalize(name: str) -> str:
    """Collapse whitespace so comparison is insensitive to spacing."""
    return " ".join(name.strip().split())


def to_iso2(name: str) -> str:
    """Return the ISO-3166-1 alpha-2 code for a country name.

    Raises :class:`UnmappedCountryError` (never returns ``None``) when the
    name cannot be mapped.
    """
    key = _normalize(name)
    if key in ALIASES:
        return ALIASES[key]
    for field in ("name", "official_name", "common_name"):
        for country in pycountry.countries:
            candidate = getattr(country, field, None)
            if candidate is not None and _normalize(candidate) == key:
                return country.alpha_2
    raise UnmappedCountryError(f"unmapped country name: {name!r}")
