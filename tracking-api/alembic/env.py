import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# also load monorepo root .env if tracking-api .env missing
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer DATABASE_URL from environment; fall back to alembic.ini
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

from app.database import Base  # noqa: E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    version_table = config.get_main_option("version_table") or "alembic_version"
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}, version_table=version_table)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    version_table = config.get_main_option("version_table") or "alembic_version"
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, version_table=version_table)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
