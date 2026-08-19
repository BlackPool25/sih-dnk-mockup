from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.classification import ClassificationError, classify_item, classify_order
from app.models import Base, CountryRate, HsCode, Lane, ProductCategory
from app.schemas import PricingItem


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


def _item(
    category_slug: str = "jute-products",
    item_id: str = "item-1",
) -> PricingItem:
    return PricingItem(
        item_id=item_id,
        category_slug=category_slug,
        quantity=1,
        unit_weight_g=500,
        dimensions_cm={
            "length_cm": "20",
            "width_cm": "15",
            "height_cm": "5",
        },
        unit_value={
            "amount_minor": 10000,
            "currency": "INR",
        },
        splittable=True,
    )


def test_classify_item_returns_category_and_hs_code(
    session: Session,
) -> None:
    result = classify_item(
        session=session,
        item=_item(),
    )

    assert result["item_id"] == "item-1"
    assert result["classification_status"] == "classified"

    assert result["category"]["slug"] == "jute-products"
    assert result["category"]["name"] == "Jute products"

    assert result["hs_code"]["hs6"] == "5310"
    assert result["hs_code"]["itc_hs_8"] == "53101091"


def test_classify_item_preserves_provenance(
    session: Session,
) -> None:
    result = classify_item(
        session=session,
        item=_item(),
    )

    assert (
        result["provenance"]["category"]["source_url"]
        == "https://example.test/categories"
    )

    assert (
        result["provenance"]["hs_code"]["source_url"]
        == "https://example.test/hs"
    )


def test_classify_item_rejects_unknown_category(
    session: Session,
) -> None:
    with pytest.raises(
        ClassificationError,
        match="No product category found",
    ):
        classify_item(
            session=session,
            item=_item(category_slug="unknown-product"),
        )


def test_classify_item_returns_category_only_when_hs_is_missing(
    session: Session,
) -> None:
    session.query(HsCode).delete()
    session.commit()

    result = classify_item(
        session=session,
        item=_item(),
    )

    assert result["classification_status"] == "category_only"
    assert result["hs_code"] is None
    assert result["provenance"]["hs_code"] is None


def test_classify_order_classifies_multiple_items(
    session: Session,
) -> None:
    items = [
        _item(item_id="item-1"),
        _item(item_id="item-2"),
    ]

    results = classify_order(
        session=session,
        items=items,
    )

    assert len(results) == 2
    assert results[0]["item_id"] == "item-1"
    assert results[1]["item_id"] == "item-2"
    assert results[0]["classification_status"] == "classified"
    assert results[1]["classification_status"] == "classified"