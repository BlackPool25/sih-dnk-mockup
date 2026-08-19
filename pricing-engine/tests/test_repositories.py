from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, CountryRate, HsCode, Lane, ProductCategory
from app.repositories import (
    get_lane,
    list_lanes,
    lookup_country_rates,
    lookup_hs_codes,
    search_categories,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        category = ProductCategory(
            slug="jute-products",
            name="Jute products",
            hs6_default="5310",
            pbe_desc_template="Jute item",
            certifications={"need": "none"},
            lane_fit={"typical_weight": "light"},
            source_url="https://example.test/categories",
            source_level="L2",
            confidence="high",
            is_estimate=False,
            effective_from=date(2026, 1, 1),
        )
        session.add(category)
        session.flush()

        session.add(
            HsCode(
                hs6="5310",
                itc_hs_8="53101091",
                hts_10=None,
                description="Jute woven fabrics",
                product_cat=category.id,
                source_url="https://example.test/hs",
                source_level="L2",
                confidence="high",
                is_estimate=False,
            )
        )
        session.add(
            CountryRate(
                country_iso2="US",
                hs6="5310",
                rate_type="MFN",
                rate_pct=Decimal("4.5000"),
                amount_minor=None,
                threshold_minor=None,
                currency="USD",
                basis="MFN",
                source_url="https://example.test/rates",
                source_level="L2",
                confidence="moderate",
                is_estimate=False,
            )
        )
        session.add(
            Lane(
                lane="ITPS",
                country_iso2="US",
                first_slab_g=50,
                first_slab_rate_minor=10000,
                addl_slab_g=50,
                addl_slab_rate_minor=2000,
                weight_cap_g=5000,
                volume_free=True,
                divisor=None,
                transit_min_days=18,
                transit_max_days=28,
                conflicts=None,
                source_url="https://example.test/lanes",
                source_level="L1",
                confidence="high",
                is_estimate=False,
            )
        )
        session.commit()

        yield session


def test_search_categories_returns_matching_categories(session: Session) -> None:
    results = search_categories(session, "jute")

    assert results == [
        {
            "slug": "jute-products",
            "name": "Jute products",
            "hs6_default": "5310",
            "pbe_desc_template": "Jute item",
            "certifications": {"need": "none"},
            "lane_fit": {"typical_weight": "light"},
            "provenance": {
                "source_url": "https://example.test/categories",
                "source_level": "L2",
                "confidence": "high",
                "is_estimate": False,
                "effective_from": "2026-01-01",
            },
        }
    ]


def test_lookup_hs_codes_returns_category_slug(session: Session) -> None:
    results = lookup_hs_codes(session, category_slug="jute-products")

    assert results[0]["hs6"] == "5310"
    assert results[0]["itc_hs_8"] == "53101091"
    assert results[0]["category_slug"] == "jute-products"
    assert results[0]["provenance"]["source_url"] == "https://example.test/hs"


def test_lookup_country_rates_returns_decimal_as_string(session: Session) -> None:
    results = lookup_country_rates(session, "US", hs6="5310")

    assert results[0]["country_iso2"] == "US"
    assert results[0]["rate_type"] == "MFN"
    assert results[0]["rate_pct"] == "4.5000"
    assert results[0]["currency"] == "USD"


def test_list_lanes_returns_country_lanes(session: Session) -> None:
    results = list_lanes(session, "US")

    assert results[0]["lane"] == "ITPS"
    assert results[0]["weight_cap_g"] == 5000
    assert results[0]["provenance"]["source_level"] == "L1"


def test_get_lane_returns_matching_lane(session: Session) -> None:
    result = get_lane(session, "US", "ITPS")

    assert result["lane"] == "ITPS"
    assert result["country_iso2"] == "US"


def test_get_lane_raises_for_missing_lane(session: Session) -> None:
    with pytest.raises(LookupError, match="no EMS lane"):
        get_lane(session, "US", "EMS")