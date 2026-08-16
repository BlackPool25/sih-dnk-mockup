"""Backend-core SQLAlchemy models.

DeclarativeBase for all backend-core table definitions.
Models are registered below (lazy imports after Base to avoid circular deps).
"""

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    """Timezone-aware UTC now, for Python-side defaults."""
    return datetime.now(UTC)

try:
    from auth.models import Base as AuthBase
    class Base(DeclarativeBase):
        metadata = AuthBase.metadata
except ImportError:
    class Base(DeclarativeBase):
        pass

from app.models.doc_pack import DocPack
from app.models.order import Order, OrderStatus
from app.models.profile import SellerProfile
from app.models.profile_document import DocumentType, ProfileDocument

__all__ = [
    "Base",
    "DocPack",
    "DocumentType",
    "Order",
    "OrderStatus",
    "ProfileDocument",
    "SellerProfile",
    "utcnow",
]
