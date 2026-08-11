import os

import redis.asyncio as redis

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Return a lazily-initialised async Redis client backed by a connection pool.

    Connects on first call using REDIS_URL from the environment. Subsequent
    calls return the same client instance.

    Returns:
        redis.asyncio.Redis: A connected async Redis client.

    Raises:
        ValueError: If the ``REDIS_URL`` environment variable is not set.
        ConnectionError: If the Redis server is unreachable or the URL is
            malformed.
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    url = os.environ.get("REDIS_URL")
    if not url:
        raise ValueError("REDIS_URL environment variable is not set")

    try:
        pool = redis.ConnectionPool.from_url(url)
        _redis_client = redis.Redis(connection_pool=pool)
    except Exception as exc:
        raise ConnectionError(f"Redis connection failed at {url}") from exc

    return _redis_client
