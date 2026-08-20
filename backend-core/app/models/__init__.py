"""Backend-core SQLAlchemy models.

``Base`` is auth's declarative base (shared metadata): the profile FK
references the auth ``users`` table, so both must live on ONE metadata for the
FK to resolve.

Orders and doc packs no longer live here — the unified ``orders`` table and all
document generation live in validation-engine.  backend-core only keeps the
seller profile and KYC-document models.
"""

from datetime import UTC, datetime

from auth.models import Base


def utcnow() -> datetime:
    """Timezone-aware UTC now, for Python-side defaults."""
    return datetime.now(UTC)


# Register models on Base.metadata — must follow Base definition to avoid
# circular imports (models import Base from here, then we re-import them).
from app.models.profile import SellerProfile
from app.models.profile_document import DocumentType, ProfileDocument
from app.models.sahayak_scan import SahayakScan

__all__ = [
    "Base",
    "DocumentType",
    "ProfileDocument",
    "SahayakScan",
    "SellerProfile",
    "utcnow",
]
