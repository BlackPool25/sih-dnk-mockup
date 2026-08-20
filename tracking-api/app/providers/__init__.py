import os

from .mock_provider import MockProvider
from .real_provider import RealProvider


def _parse_mock_tracking(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in ("true", "1", "yes")


def _is_mock_tracking_enabled() -> bool:
    return _parse_mock_tracking(os.getenv("MOCK_TRACKING"))


def get_provider():
    # MOCK_TRACKING env alias takes precedence over TRACKING_PROVIDER
    if _is_mock_tracking_enabled():
        return MockProvider()
    provider_type = os.getenv("TRACKING_PROVIDER", "mock").strip().lower()
    if provider_type == "mock":
        return MockProvider()
    elif provider_type in ("live", "17track"):
        return RealProvider()
    else:
        raise ValueError(f"Unknown TRACKING_PROVIDER: {provider_type}")
