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
    FillingRule,
    HsCode,
    PbeFieldSchema,
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


def test_rules_seed_idempotent() -> None:
    """import_configs(rules=True) twice — exactly 8 filling_rules rows both times."""
    for _ in range(2):
        import_configs(categories=False, states=False, flags=False, pbe=False, rules=True)
        with SessionLocal() as session:
            n = session.scalar(select(func.count()).select_from(FillingRule)) or 0
        assert n == 8


def test_rules_alone_truncate_scope() -> None:
    """--rules ALONE must not truncate pbe_field_schemas or config_flags."""
    with SessionLocal() as session:
        pbe_before = session.scalar(select(func.count()).select_from(PbeFieldSchema)) or 0
        flags_before = session.scalar(select(func.count()).select_from(ConfigFlag)) or 0

    import_configs(categories=False, states=False, flags=False, pbe=False, rules=True)

    with SessionLocal() as session:
        pbe_after = session.scalar(select(func.count()).select_from(PbeFieldSchema)) or 0
        flags_after = session.scalar(select(func.count()).select_from(ConfigFlag)) or 0
    assert pbe_after == pbe_before == 116
    assert flags_after == flags_before == 86
