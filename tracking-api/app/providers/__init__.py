import os
from .mock_provider import MockProvider
from .real_provider import RealProvider

def get_provider():
    provider_type = os.getenv("TRACKING_PROVIDER", "mock")
    if provider_type == "mock":
        return MockProvider()
    elif provider_type == "live":
        return RealProvider()
    else:
        raise ValueError(f"Unknown TRACKING_PROVIDER: {provider_type}")