import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    database_url: str | None = Field(default=None)
    redis_url: str | None = Field(default=None)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith("postgresql"):
            raise ValueError("DATABASE_URL must start with 'postgresql'")
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith("redis://"):
            raise ValueError("REDIS_URL must start with 'redis://'")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL"),
        redis_url=os.environ.get("REDIS_URL"),
    )