"""Backend-core Alembic environment configuration.

Loads .env from repo root, sets DATABASE_URL, and uses backend-core's
Base.metadata for autogenerate.  The version_table is ``core_alembic_version``
to keep migration history separate from auth and validation-engine.

Tables from other services (users, refresh_tokens) are reflected into
target_metadata for FK resolution but excluded from the migration diff
via the _CORE_TABLES whitelist in include_name().
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Table, engine_from_config, pool
from sqlalchemy.dialects.postgresql import UUID

from alembic import context

# Make the monorepo root importable so ``from app.models import Base`` resolves.
BACKEND_CORE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_CORE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load .env from the repo root (shared DATABASE_URL/JWT keys etc.).
load_dotenv(REPO_ROOT / ".env")

# Alembic Config object
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Backend-core model MetaData — imported so autogenerate sees them when
# models are added.  Tables below come from model classes registered in
# app.models.__init__.py.
from app.models import Base

target_metadata = Base.metadata

# ── Tables owned by backend-core (whitelist for autogenerate diff) ──────────
# Any table reflected into target_metadata for FK resolution will NOT appear
# in the migration diff unless listed here.
_CORE_TABLES = frozenset({"seller_profiles", "profile_documents", "orders", "doc_packs"})


def include_object(
    obj: object,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: object | None,
) -> bool:
    """Filter autogenerate to only backend-core-owned tables.

    Without this, autogenerate sees auth/validation-engine tables in the
    DB as "removed" and tries to drop them — those tables live in separate
    metadata spaces (different version_table).

    Uses a whitelist (_CORE_TABLES) so that tables reflected for FK
    resolution (e.g. users) are not included in the diff.
    """
    if type_ == "table":
        return name in _CORE_TABLES
    return True


def _reflect_foreign_targets(connection) -> None:
    """Reflect tables from other services that backend-core FKs reference.

    Without this, SQLAlchemy cannot resolve ForeignKey('users.id') during
    autogenerate ``sorted_tables`` and raises NoReferencedTableError.
    """
    Table(
        "users",
        target_metadata,
        autoload_with=connection,
        extend_existing=True,
    )


def _stub_foreign_targets() -> None:
    """Create minimal stub tables for FK resolution in offline mode.

    Offline mode has no DB connection to auto-load column metadata, but
    autogenerate still needs to resolve ForeignKey targets.  These stubs
    provide just enough for constraint ordering.
    """
    from sqlalchemy import Column

    Table(
        "users",
        target_metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        extend_existing=True,
    )


def _is_autogenerate() -> bool:
    """Return True when alembic is running ``revision --autogenerate``.

    During autogenerate we need (a) foreign-key targets reflected into
    metadata for constraint ordering, and (b) include_object to filter
    those reflected tables out of the generated migration script.

    During regular upgrade/downgrade we skip both — the migration script
    already contains the correct DDL and filtering is unnecessary.
    """
    return getattr(context.config.cmd_opts, "autogenerate", False)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    if _is_autogenerate():
        _stub_foreign_targets()

    url = config.get_main_option("sqlalchemy.url")
    ctx_kwargs = {
        "url": url,
        "target_metadata": target_metadata,
        "literal_binds": True,
        "dialect_opts": {"paramstyle": "named"},
        "version_table": "core_alembic_version",
    }
    if _is_autogenerate():
        ctx_kwargs["include_object"] = include_object

    context.configure(**ctx_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Reflect foreign-key targets only during autogenerate — otherwise
        # the reflected table would be added to metadata and autogenerate
        # would include it in the migration script (even with include_object
        # filtering comparison; it can still affect upgrade execution).
        if _is_autogenerate():
            _reflect_foreign_targets(connection)

        ctx_kwargs = {
            "connection": connection,
            "target_metadata": target_metadata,
            "version_table": "core_alembic_version",
        }
        if _is_autogenerate():
            ctx_kwargs["include_object"] = include_object

        context.configure(**ctx_kwargs)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
