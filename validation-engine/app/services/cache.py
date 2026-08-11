import os
import redis
import json
from typing import Any, Callable

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
KEY_PREFIX = "validation:"
DEFAULT_TTL = 300  # 5 minutes

class RedisCache:
    def __init__(self, redis_url: str = REDIS_URL, key_prefix: str = KEY_PREFIX, ttl: int = DEFAULT_TTL):
        self.key_prefix = key_prefix
        self.ttl = ttl
        self._redis: redis.Redis | None = None
        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            self._redis = None  # graceful fallback
    
    def _key(self, name: str) -> str:
        return f"{self.key_prefix}{name}"
    
    def get(self, key: str) -> Any | None:
        if self._redis is None:
            return None  # fallback to DB
        try:
            value = self._redis.get(self._key(key))
            return json.loads(value) if value else None
        except (redis.ConnectionError, redis.TimeoutError):
            return None
    
    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        if self._redis is None:
            return False
        try:
            self._redis.setex(
                self._key(key),
                ttl or self.ttl,
                json.dumps(value, default=str)
            )
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False
    
    def delete(self, key: str) -> bool:
        if self._redis is None:
            return False
        try:
            self._redis.delete(self._key(key))
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False
    
    def flush(self) -> bool:
        """Flush all keys with this cache's prefix."""
        if self._redis is None:
            return False
        try:
            keys = self._redis.keys(f"{self.key_prefix}*")
            if keys:
                self._redis.delete(*keys)
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False
    
    def get_config_version(self) -> str:
        """Get current config version for invalidation."""
        return self.get("config_version") or "0"
    
    def bump_config_version(self) -> bool:
        """Increment config version — invalidates all cached config reads."""
        try:
            current = int(self.get_config_version())
            return self.set("config_version", str(current + 1))
        except (ValueError, TypeError):
            return self.set("config_version", "1")
    
    @property
    def available(self) -> bool:
        return self._redis is not None


# Module-level singleton
cache = RedisCache()
