"""Tests for storage.db — engine creation and session factory.

load_dotenv() in db.py runs at import-time and may pull DATABASE_URL from a
project .env file.  Tests use ``os.environ["DATABASE_URL"] = ""`` to override
any .env value (load_dotenv does not override existing env vars).
"""

import os

import pytest

from storage.db import get_engine, get_session


class TestGetEngine:
    def test_raises_valueerror_when_databse_url_unset(self) -> None:
        os.environ["DATABASE_URL"] = ""
        try:
            with pytest.raises(ValueError, match="DATABASE_URL not set"):
                get_engine()
        finally:
            del os.environ["DATABASE_URL"]

    def test_returns_engine_when_url_set(self) -> None:
        os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/test"
        try:
            engine = get_engine()
            assert engine is not None
            assert engine.name == "postgresql"
        finally:
            del os.environ["DATABASE_URL"]


class TestGetSession:
    def test_returns_async_sessionmaker(self) -> None:
        os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/test"
        try:
            sessionmaker = get_session()
            assert sessionmaker is not None
            assert callable(sessionmaker)
        finally:
            del os.environ["DATABASE_URL"]

    def test_raises_valueerror_when_url_unset(self) -> None:
        os.environ["DATABASE_URL"] = ""
        try:
            with pytest.raises(ValueError, match="DATABASE_URL not set"):
                get_session()
        finally:
            del os.environ["DATABASE_URL"]
