import os
import redis
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

CACHE_TTL_SECONDS = 30

def get_cached_shipment(tracking_number: str):
    data = r.get(f"shipment:{tracking_number}")
    return json.loads(data) if data else None

def set_cached_shipment(tracking_number: str, shipment_data: dict[str, object]) -> None:
    r.setex(f"shipment:{tracking_number}", CACHE_TTL_SECONDS, json.dumps(shipment_data))

def invalidate_shipment_cache(tracking_number: str):
    r.delete(f"shipment:{tracking_number}")