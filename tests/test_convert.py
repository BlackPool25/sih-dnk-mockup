"""Tests for ``app.services.convert`` — truncate-scope behaviour.

These hit the LIVE seeded DB (no fixtures — the container must be up, and the
DB must be fully seeded first).  The pinned regression: ``--pbe`` ALONE must
re-seed only pbe_field_schemas — previously the shared CONFIG_TRUNCATE wiped
all six config tables on every invocation (todo 13 gotcha).
"""

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import (
    ConfigFlag,
    CountryRate,
    HsCode,
    ProductCategory,
    StateSalesTax,
)
from app.services.convert import import_configs

_TABLES = (
    (ProductCategory, "product_categories"),
    (HsCode, "hs_codes"),
    (CountryRate, "country_rates"),
    (StateSalesTax, "state_sales_tax"),
    (ConfigFlag, "config_flags"),
)


def _counts() -> dict[str, int]:
    with SessionLocal() as session:
        return {
            table_name: session.scalar(select(func.count()).select_from(model)) or 0
            for model, table_name in _TABLES
        }


def test_pbe_alone_leaves_other_config_tables_untouched() -> None:
    """Regression: --pbe ALONE must not truncate categories/states/flags/hs/rates."""
    before = _counts()
    assert all(v > 0 for v in before.values()), "DB not fully seeded — run --all first"

    import_configs(categories=False, states=False, flags=False, pbe=True)

    after = _counts()
    assert after == before


def test_states_alone_leaves_other_config_tables_untouched() -> None:
    """--states ALONE must not truncate categories/flags/pbe/hs/rates."""
    before = _counts()
    assert all(v > 0 for v in before.values()), "DB not fully seeded — run --all first"

    import_configs(categories=False, states=True, flags=False, pbe=False)

    after = _counts()
    assert after == before
