"""Model registry — importing this module registers every table on Base.metadata.

Alembic autogenerate must see ALL models; importing them here (and importing
this package from alembic/env.py) guarantees that.
"""

from app.models.base import Base, ProvenanceMixin
from app.models.config_flags import ConfigFlag
from app.models.country_rates import CountryRate
from app.models.documents import Document
from app.models.filling_rules import FillingRule
from app.models.hs_codes import HsCode
from app.models.lanes import Lane
from app.models.lookups import Lookup
from app.models.pbe_field_schemas import PbeFieldSchema
from app.models.product_categories import ProductCategory
from app.models.state_sales_tax import StateSalesTax
from app.models.transcripts import Transcript

__all__ = [
    "Base",
    "ConfigFlag",
    "CountryRate",
    "Document",
    "FillingRule",
    "HsCode",
    "Lane",
    "Lookup",
    "PbeFieldSchema",
    "ProductCategory",
    "ProvenanceMixin",
    "StateSalesTax",
    "Transcript",
]
