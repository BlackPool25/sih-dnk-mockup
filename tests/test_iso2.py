"""Unit tests for ``app.parsers.iso2``.

Pins the 11 corpus aliases to their ISO-3166-1 alpha-2 codes and checks
that pycountry resolves the plain country names.  A wrong alias mapping
fails these tests — which is exactly what the 135/135 ITPS import gate
also enforces at seed time.
"""

import pycountry
import pytest

from app.parsers.iso2 import UnmappedCountryError, to_iso2

# The 11 pinned alias spellings from the corpus tables.
PINNED_ALIASES = {
    "Great Britain (UK)": "GB",
    "Korea (Republic of)": "KR",
    "Türkiye": "TR",
    "Cote d'Ivoire": "CI",
    "Macao (China)": "MO",
    "Russian Federation": "RU",
    "Vietnam": "VN",
    "Czechia": "CZ",
    "Eswatini": "SZ",
    "United States of America": "US",
    "United Arab Emirates": "AE",
}

# Plain names that pycountry must resolve on its own.
PLAIN_NAMES = {
    "Afghanistan": "AF",
    "Australia": "AU",
    "Canada": "CA",
    "Germany": "DE",
    "India": "IN",
    "Japan": "JP",
    "New Zealand": "NZ",
    "Singapore": "SG",
    "South Africa": "ZA",
    "Zimbabwe": "ZW",
}


@pytest.mark.parametrize("name,expected", sorted(PINNED_ALIASES.items()))
def test_pinned_aliases(name: str, expected: str) -> None:
    """Every pinned corpus alias must resolve to its ISO2 code."""
    assert to_iso2(name) == expected


@pytest.mark.parametrize("name,expected", sorted(PLAIN_NAMES.items()))
def test_pycountry_plain_names(name: str, expected: str) -> None:
    """Plain names must resolve via pycountry to the expected ISO2 code."""
    assert to_iso2(name) == expected


@pytest.mark.parametrize("name,expected", sorted(PINNED_ALIASES.items()))
def test_alias_targets_are_real_countries(name: str, expected: str) -> None:
    """Alias targets must be valid ISO-3166-1 alpha-2 codes pycountry knows."""
    assert pycountry.countries.get(alpha_2=expected) is not None


def test_unmapped_name_raises() -> None:
    """An unmapped name must raise — never return None."""
    with pytest.raises(UnmappedCountryError):
        to_iso2("Westeros")


def test_no_missing_alias_entries() -> None:
    """Every pinned alias must actually live in the ALIASES map.

    If a pinned name falls through to pycountry (i.e. the alias map is
    incomplete), a later wrong alias for that name could go unnoticed.
    """
    from app.parsers.iso2 import ALIASES

    assert PINNED_ALIASES.keys() <= ALIASES.keys()
