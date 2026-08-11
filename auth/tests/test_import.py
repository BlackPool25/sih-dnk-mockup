"""
Basic import smoke tests for the auth package.
Verifies that the auth package, its sub-packages, and storage dependencies
are importable without errors.

NOTE: storage.config auto-instantiates Settings() at module level.
Tests that import it must set required env vars first.
"""

import os


def test_import_auth_package():
    """All auth sub-packages should be importable."""
    import auth
    import auth.models
    import auth.services
    import auth.routes
    import auth.middleware
    import auth.cli

    assert auth is not None


def test_import_storage_db_and_redis():
    """DB and Redis symbols must be reachable (no env vars needed)."""
    from storage.db import get_engine, get_session
    from storage.redis import get_redis

    assert callable(get_engine)
    assert callable(get_session)
    assert callable(get_redis)


def test_import_storage_config():
    """Settings import requires env vars (auto-instantiated singleton)."""
    os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault(
        "ENCRYPTION_MASTER_KEY",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-at-least-32-chars-long")
    os.environ.setdefault("SAHAYAK_EMAIL", "test@test.com")
    os.environ.setdefault("SAHAYAK_PASSWORD", "test123")
    os.environ.setdefault("DEMO_SELLER_EMAIL", "seller@test.com")
    os.environ.setdefault("DEMO_SELLER_PASSWORD", "test123")
    os.environ.setdefault("DEMO_BUYER_EMAIL", "buyer@test.com")
    os.environ.setdefault("DEMO_BUYER_PASSWORD", "test123")

    from storage.config import settings

    assert settings.DATABASE_URL.startswith("postgresql")

    # Also verify JWT and passlib are importable
    import jwt
    import passlib

    assert jwt.__version__
    assert passlib.__version__
