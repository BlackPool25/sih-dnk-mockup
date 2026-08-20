"""Shared configuration for SIH-DNK microservices.

Loads all env vars from the project ``.env`` file via python-dotenv,
then populates a pydantic BaseModel with field-level validators.

Export::

    from storage.config import settings
    settings.DATABASE_URL  # etc.
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

load_dotenv()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_rate_limit(raw: str) -> tuple[int, int]:
    """Parse a rate-limit string like ``'5,60'`` into (max_requests, window_seconds)."""
    parts = raw.split(",")
    if len(parts) != 2:
        raise ValueError(f"Rate limit must be 'N,M' format, got: {raw!r}")
    try:
        max_req = int(parts[0].strip())
        window = int(parts[1].strip())
    except ValueError:
        raise ValueError(f"Rate limit values must be integers, got: {raw!r}") from None
    if max_req < 0 or window <= 0:
        raise ValueError(
            f"Rate limit must have non-negative count and positive window, got: {raw!r}"
        )
    return max_req, window


# ---------------------------------------------------------------------------
# Settings model
# ---------------------------------------------------------------------------


class Settings(BaseModel):
    """Application-wide configuration populated from environment variables.

    Instantiate without arguments to read from ``os.environ`` (after
    ``load_dotenv()`` above).  Pass keyword arguments to bypass env lookup
    (used by tests).
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    # -- Database & cache ------------------------------------------------------
    DATABASE_URL: str
    REDIS_URL: str

    # -- Encryption & auth -----------------------------------------------------
    ENCRYPTION_MASTER_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DOC_ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    APP_BASE_URL: str = "http://localhost:8000"

    # -- Rate limits -----------------------------------------------------------
    RATE_LIMIT_LOGIN: str = Field(default="5,60")
    RATE_LIMIT_REGISTER: str = Field(default="3,60")
    RATE_LIMIT_DEFAULT: str = Field(default="100,60")

    # -- Pre-seeded accounts ---------------------------------------------------
    SAHAYAK_EMAIL: str
    SAHAYAK_PASSWORD: str
    DEMO_SELLER_EMAIL: str
    DEMO_SELLER_PASSWORD: str
    DEMO_BUYER_EMAIL: str
    DEMO_BUYER_PASSWORD: str

    # -- LLM -------------------------------------------------------------------
    LLM_CONVERSATION_TTL_HOURS: int = 24

    # Optional keys — absent ⇒ RuleDraftExtractor + template replies (no network).
    GEMINI_API_KEY: str | None = None
    SARVAM_API_KEY: str | None = None
    SARVAM_ENABLED: bool = False

    # -- Downstream engine URLs ------------------------------------------------
    VALIDATION_ENGINE_URL: str = "http://validation-engine:8000"
    PRICING_ENGINE_URL: str = "http://pricing-engine:8000"
    TRACKING_API_URL: str = "http://tracking-api:8000"
    VOICE_PIPELINE_URL: str = "http://voice-pipeline:8000"
    MARKETPLACE_URL: str = "http://marketplace:8000"
    MESSAGING_SERVICE_URL: str = "http://messaging-service:8000"

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError(f"DATABASE_URL must start with 'postgresql', got: {v!r}")
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def _validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError(f"REDIS_URL must start with 'redis://', got: {v!r}")
        return v

    @field_validator("ENCRYPTION_MASTER_KEY")
    @classmethod
    def _validate_encryption_key(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdefABCDEF" for c in v):
            raise ValueError("ENCRYPTION_MASTER_KEY must be exactly 64 hex characters")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(f"JWT_SECRET_KEY must be at least 32 chars, got {len(v)}")
        return v

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def _validate_jwt_algorithm(cls, v: str) -> str:
        allowed = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}
        if v not in allowed:
            raise ValueError(f"JWT_ALGORITHM must be one of {sorted(allowed)}, got: {v!r}")
        return v

    @field_validator(
        "RATE_LIMIT_LOGIN",
        "RATE_LIMIT_REGISTER",
        "RATE_LIMIT_DEFAULT",
    )
    @classmethod
    def _validate_rate_limit_format(cls, v: str) -> str:
        _parse_rate_limit(v)  # raises on invalid format
        return v

    # --------------------------------------------------------------------------
    # Auto-init from environment
    # --------------------------------------------------------------------------

    def __init__(self, **data: object) -> None:
        if not data:
            # Read from os.environ when no explicit arguments are given.
            env_data: dict[str, object] = {}
            for field_name in type(self).model_fields:
                env_val = os.environ.get(field_name)
                if env_val is not None:
                    env_data[field_name] = env_val
            data = env_data
        super().__init__(**data)

    # --------------------------------------------------------------------------
    # Derived properties (rate limits as (int, int) tuples)
    # --------------------------------------------------------------------------

    @computed_field
    def RATE_LIMIT_LOGIN_TUPLE(self) -> tuple[int, int]:
        return _parse_rate_limit(self.RATE_LIMIT_LOGIN)

    @computed_field
    def RATE_LIMIT_REGISTER_TUPLE(self) -> tuple[int, int]:
        return _parse_rate_limit(self.RATE_LIMIT_REGISTER)

    @computed_field
    def RATE_LIMIT_DEFAULT_TUPLE(self) -> tuple[int, int]:
        return _parse_rate_limit(self.RATE_LIMIT_DEFAULT)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

settings = Settings()
