"""Config flags (config table, carries provenance).

flag_value is a JSONB scalar (number/string/bool) or flat array — never an
object wrapper (pinned by the verification gates).
"""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class ConfigFlag(ProvenanceMixin, Base):
    __tablename__ = "config_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    flag_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    flag_value: Mapped[object] = mapped_column(JSONB, nullable=False)
