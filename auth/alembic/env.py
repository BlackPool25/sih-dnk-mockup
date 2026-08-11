import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the auth package importable so `models` resolves regardless of cwd.
AUTH_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = AUTH_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load .env from the repo root (shared DATABASE_URL).
load_dotenv(REPO_ROOT / ".env")

# This is the Alembic Config object, which provides access to the values
# within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Add auth's model MetaData object for 'autogenerate' support.
# Must be auth.models.Base, NOT validation-engine's Base.
from auth.models import Base  # noqa: E402

target_metadata = Base.metadata


def include_name(name: str, type_: str, parent_names: dict[str, str]) -> bool:
    """Filter autogenerate to only auth-owned objects.

    Without this, autogenerate sees every validation-engine table in the
    DB as "removed" and tries to drop them — those tables live in a
    different metadata space (different version_table).
    """
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="auth_alembic_version",
        include_name=include_name,
    )

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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="auth_alembic_version",
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
