from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required for database access")
    return create_engine(settings.database_url, pool_pre_ping=True)
@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def create_session() -> Session:
    return get_session_factory()()