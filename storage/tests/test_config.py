"""Tests for storage.config — Settings model, validators, defaults, and singleton."""

import os

import pytest
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Set required env vars *before* doing any import from storage.config so the
# module-level `settings = Settings()` singleton doesn't raise at import time.
# ---------------------------------------------------------------------------
_VALID_ENV = {
    "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5433/db",
    "REDIS_URL": "redis://localhost:6379/0",
    "ENCRYPTION_MASTER_KEY": "a" * 64,
    "JWT_SECRET_KEY": "x" * 32,
    "SAHAYAK_EMAIL": "sahayak@example.com",
    "SAHAYAK_PASSWORD": "sahayak-pass-123",
    "DEMO_SELLER_EMAIL": "seller@example.com",
    "DEMO_SELLER_PASSWORD": "seller-pass-456",
    "DEMO_BUYER_EMAIL": "buyer@example.com",
    "DEMO_BUYER_PASSWORD": "buyer-pass-789",
}

for _k, _v in _VALID_ENV.items():
    os.environ[_k] = _v

from storage.config import Settings, _parse_rate_limit, settings

# ---------------------------------------------------------------------------
# Helper: minimal valid constructor kwargs
# ---------------------------------------------------------------------------


def _valid_kwargs(**overrides: str) -> dict[str, object]:
    """Return a dict of valid kwargs for Settings(), with optional overrides."""
    base: dict[str, object] = {
        "DATABASE_URL": "postgresql+psycopg://u:p@localhost/db",
        "REDIS_URL": "redis://localhost:6379/0",
        "ENCRYPTION_MASTER_KEY": "b" * 64,
        "JWT_SECRET_KEY": "y" * 32,
        "SAHAYAK_EMAIL": "s@t.com",
        "SAHAYAK_PASSWORD": "p1",
        "DEMO_SELLER_EMAIL": "ds@t.com",
        "DEMO_SELLER_PASSWORD": "p2",
        "DEMO_BUYER_EMAIL": "db@t.com",
        "DEMO_BUYER_PASSWORD": "p3",
    }
    base.update(overrides)
    return base


# ===========================================================================
# Module-level singleton
# ===========================================================================


class TestModuleSingleton:
    """The module-level ``settings`` singleton is created at import time."""

    def test_settings_is_settings_instance(self) -> None:
        assert isinstance(settings, Settings)

    def test_settings_reads_database_url_from_env(self) -> None:
        assert settings.DATABASE_URL.startswith("postgresql")

    def test_settings_reads_redis_url_from_env(self) -> None:
        assert settings.REDIS_URL.startswith("redis://")


# ===========================================================================
# Defaults
# ===========================================================================


class TestDefaults:
    """All fields with default values work when not explicitly provided."""

    def test_jwt_algorithm_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.JWT_ALGORITHM == "HS256"

    def test_access_token_expire_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 120

    def test_refresh_token_expire_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_doc_access_token_expire_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.DOC_ACCESS_TOKEN_EXPIRE_DAYS == 30

    def test_rate_limit_login_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.RATE_LIMIT_LOGIN == "5,60"

    def test_rate_limit_register_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.RATE_LIMIT_REGISTER == "3,60"

    def test_rate_limit_default_field_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.RATE_LIMIT_DEFAULT == "100,60"

    def test_llm_conversation_ttl_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.LLM_CONVERSATION_TTL_HOURS == 24

    def test_validation_engine_url_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.VALIDATION_ENGINE_URL == "http://validation-engine:8000"

    def test_pricing_engine_url_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.PRICING_ENGINE_URL == "http://pricing-engine:8000"

    def test_tracking_api_url_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.TRACKING_API_URL == "http://tracking-api:8000"

    def test_voice_pipeline_url_default(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.VOICE_PIPELINE_URL == "http://voice-pipeline:8000"


# ===========================================================================
# Valid values
# ===========================================================================


class TestValidValues:
    """All fields accept their expected valid values."""

    def test_database_url_postgresql(self) -> None:
        s = Settings(**_valid_kwargs(DATABASE_URL="postgresql://user:pass@host/db"))
        assert s.DATABASE_URL == "postgresql://user:pass@host/db"

    def test_database_url_with_psycopg_driver(self) -> None:
        s = Settings(**_valid_kwargs(DATABASE_URL="postgresql+psycopg://user:pass@host/db"))
        assert s.DATABASE_URL == "postgresql+psycopg://user:pass@host/db"

    def test_redis_url_valid(self) -> None:
        s = Settings(**_valid_kwargs(REDIS_URL="redis://redis:6379/1"))
        assert s.REDIS_URL == "redis://redis:6379/1"

    def test_encryption_key_valid_64_hex_lower(self) -> None:
        s = Settings(**_valid_kwargs(ENCRYPTION_MASTER_KEY="a" * 64))
        assert s.ENCRYPTION_MASTER_KEY == "a" * 64

    def test_encryption_key_valid_64_hex_mixed_case(self) -> None:
        key = "0123456789abcdefABCDEF" * 3  # 22 * 3 = 66 chars
        key = key[:64]  # trim to exactly 64
        s = Settings(**_valid_kwargs(ENCRYPTION_MASTER_KEY=key))
        assert s.ENCRYPTION_MASTER_KEY == key

    def test_jwt_secret_min_length(self) -> None:
        s = Settings(**_valid_kwargs(JWT_SECRET_KEY="k" * 32))
        assert len(s.JWT_SECRET_KEY) == 32

    def test_jwt_secret_long(self) -> None:
        s = Settings(**_valid_kwargs(JWT_SECRET_KEY="k" * 128))
        assert len(s.JWT_SECRET_KEY) == 128

    def test_jwt_algorithm_hs256(self) -> None:
        s = Settings(**_valid_kwargs(JWT_ALGORITHM="HS256"))
        assert s.JWT_ALGORITHM == "HS256"

    def test_jwt_algorithm_rs512(self) -> None:
        s = Settings(**_valid_kwargs(JWT_ALGORITHM="RS512"))
        assert s.JWT_ALGORITHM == "RS512"

    def test_jwt_algorithm_es384(self) -> None:
        s = Settings(**_valid_kwargs(JWT_ALGORITHM="ES384"))
        assert s.JWT_ALGORITHM == "ES384"

    def test_pre_seeded_account_emails(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.SAHAYAK_EMAIL == "s@t.com"
        assert s.DEMO_SELLER_EMAIL == "ds@t.com"
        assert s.DEMO_BUYER_EMAIL == "db@t.com"

    def test_custom_engine_urls(self) -> None:
        s = Settings(
            **_valid_kwargs(
                VALIDATION_ENGINE_URL="http://custom-ve:9000",
                PRICING_ENGINE_URL="http://custom-pe:9001",
            )
        )
        assert s.VALIDATION_ENGINE_URL == "http://custom-ve:9000"
        assert s.PRICING_ENGINE_URL == "http://custom-pe:9001"


# ===========================================================================
# Missing / invalid fields
# ===========================================================================


class TestMissingRequired:
    """Required fields without defaults raise ValidationError when missing."""

    def test_missing_database_url(self) -> None:
        kwargs = _valid_kwargs()
        del kwargs["DATABASE_URL"]
        with pytest.raises(ValidationError):
            Settings(**kwargs)

    def test_missing_encryption_master_key(self) -> None:
        kwargs = _valid_kwargs()
        del kwargs["ENCRYPTION_MASTER_KEY"]
        with pytest.raises(ValidationError):
            Settings(**kwargs)

    def test_missing_jwt_secret_key(self) -> None:
        kwargs = _valid_kwargs()
        del kwargs["JWT_SECRET_KEY"]
        with pytest.raises(ValidationError):
            Settings(**kwargs)

    def test_missing_sahayak_email(self) -> None:
        kwargs = _valid_kwargs()
        del kwargs["SAHAYAK_EMAIL"]
        with pytest.raises(ValidationError):
            Settings(**kwargs)


class TestInvalidFormat:
    """Field-level validators reject malformed values."""

    def test_database_url_not_postgresql(self) -> None:
        with pytest.raises(ValidationError, match="DATABASE_URL"):
            Settings(**_valid_kwargs(DATABASE_URL="mysql://user:pass@host/db"))

    def test_database_url_empty_string(self) -> None:
        with pytest.raises(ValidationError, match="DATABASE_URL"):
            Settings(**_valid_kwargs(DATABASE_URL=""))

    def test_redis_url_not_redis(self) -> None:
        with pytest.raises(ValidationError, match="REDIS_URL"):
            Settings(**_valid_kwargs(REDIS_URL="http://redis:6379"))

    def test_encryption_key_wrong_length(self) -> None:
        with pytest.raises(ValidationError, match="ENCRYPTION_MASTER_KEY"):
            Settings(**_valid_kwargs(ENCRYPTION_MASTER_KEY="a" * 63))

    def test_encryption_key_non_hex(self) -> None:
        with pytest.raises(ValidationError, match="ENCRYPTION_MASTER_KEY"):
            Settings(**_valid_kwargs(ENCRYPTION_MASTER_KEY="g" * 64))

    def test_encryption_key_empty(self) -> None:
        with pytest.raises(ValidationError, match="ENCRYPTION_MASTER_KEY"):
            Settings(**_valid_kwargs(ENCRYPTION_MASTER_KEY=""))

    def test_jwt_secret_too_short(self) -> None:
        with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
            Settings(**_valid_kwargs(JWT_SECRET_KEY="short"))

    def test_jwt_algorithm_invalid(self) -> None:
        with pytest.raises(ValidationError, match="JWT_ALGORITHM"):
            Settings(**_valid_kwargs(JWT_ALGORITHM="NONE"))

    def test_jwt_algorithm_lowercase(self) -> None:
        with pytest.raises(ValidationError, match="JWT_ALGORITHM"):
            Settings(**_valid_kwargs(JWT_ALGORITHM="hs256"))

    def test_rate_limit_login_wrong_format(self) -> None:
        with pytest.raises(ValidationError, match="RATE_LIMIT_LOGIN"):
            Settings(**_valid_kwargs(RATE_LIMIT_LOGIN="5-60"))

    def test_rate_limit_register_non_numeric(self) -> None:
        with pytest.raises(ValidationError, match="RATE_LIMIT_REGISTER"):
            Settings(**_valid_kwargs(RATE_LIMIT_REGISTER="x,y"))

    def test_rate_limit_negative_count(self) -> None:
        with pytest.raises(ValidationError, match="RATE_LIMIT_DEFAULT"):
            Settings(**_valid_kwargs(RATE_LIMIT_DEFAULT="-1,60"))

    def test_rate_limit_zero_window(self) -> None:
        with pytest.raises(ValidationError, match="RATE_LIMIT_DEFAULT"):
            Settings(**_valid_kwargs(RATE_LIMIT_DEFAULT="5,0"))


# ===========================================================================
# Rate-limit tuple parsing (computed_field)
# ===========================================================================


class TestRateLimitTuples:
    """Computed fields expose rate limits as (int, int) tuples."""

    def test_login_tuple(self) -> None:
        s = Settings(**_valid_kwargs(RATE_LIMIT_LOGIN="10,120"))
        assert s.RATE_LIMIT_LOGIN_TUPLE == (10, 120)

    def test_register_tuple(self) -> None:
        s = Settings(**_valid_kwargs(RATE_LIMIT_REGISTER="7,30"))
        assert s.RATE_LIMIT_REGISTER_TUPLE == (7, 30)

    def test_default_tuple(self) -> None:
        s = Settings(**_valid_kwargs())
        # Default is "100,60"
        assert s.RATE_LIMIT_DEFAULT_TUPLE == (100, 60)

    def test_default_login_tuple_from_default_str(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.RATE_LIMIT_LOGIN_TUPLE == (5, 60)

    def test_default_register_tuple_from_default_str(self) -> None:
        s = Settings(**_valid_kwargs())
        assert s.RATE_LIMIT_REGISTER_TUPLE == (3, 60)

    def test_tuple_is_int_int(self) -> None:
        s = Settings(**_valid_kwargs(RATE_LIMIT_LOGIN="20,300"))
        t = s.RATE_LIMIT_LOGIN_TUPLE
        assert isinstance(t, tuple)
        assert len(t) == 2
        assert isinstance(t[0], int)
        assert isinstance(t[1], int)


# ===========================================================================
# _parse_rate_limit helper
# ===========================================================================


class TestParseRateLimit:
    """Direct tests for the module-level _parse_rate_limit helper."""

    def test_valid_simple(self) -> None:
        assert _parse_rate_limit("5,60") == (5, 60)

    def test_valid_with_spaces(self) -> None:
        assert _parse_rate_limit(" 5 , 60 ") == (5, 60)

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="N,M"):
            _parse_rate_limit("not-valid")

    def test_non_integer_values_raises(self) -> None:
        with pytest.raises(ValueError, match="integers"):
            _parse_rate_limit("x,y")

    def test_negative_count_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            _parse_rate_limit("-1,60")

    def test_zero_window_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            _parse_rate_limit("5,0")

    def test_three_parts_raises(self) -> None:
        with pytest.raises(ValueError, match="N,M"):
            _parse_rate_limit("1,2,3")


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    """Boundary and edge-case behaviour."""

    def test_encryption_key_exactly_64(self) -> None:
        s = Settings(**_valid_kwargs(ENCRYPTION_MASTER_KEY="c" * 64))
        assert len(s.ENCRYPTION_MASTER_KEY) == 64

    def test_jwt_secret_exactly_32(self) -> None:
        s = Settings(**_valid_kwargs(JWT_SECRET_KEY="s" * 32))
        assert len(s.JWT_SECRET_KEY) == 32

    def test_rate_limit_count_zero_allowed(self) -> None:
        s = Settings(**_valid_kwargs(RATE_LIMIT_DEFAULT="0,60"))
        assert s.RATE_LIMIT_DEFAULT_TUPLE == (0, 60)

    def test_rate_limit_large_window(self) -> None:
        s = Settings(**_valid_kwargs(RATE_LIMIT_DEFAULT="100,86400"))
        assert s.RATE_LIMIT_DEFAULT_TUPLE == (100, 86400)

    def test_all_jwt_algorithms_accepted(self) -> None:
        for alg in ("HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"):
            s = Settings(**_valid_kwargs(JWT_ALGORITHM=alg))
            assert s.JWT_ALGORITHM == alg

    def test_settings_is_frozen_after_creation(self) -> None:
        """Settings instances are immutable."""
        s = Settings(**_valid_kwargs())
        field_name = "JWT_ALGORITHM"
        with pytest.raises(ValidationError):
            setattr(s, field_name, "HS512")
