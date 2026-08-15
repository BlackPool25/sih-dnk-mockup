import os
from .base import TrackingProvider

class RealProvider(TrackingProvider):
    def __init__(self):
        self.api_key = os.getenv("TRACK17_API_KEY")

    def get_next_status(self, current_status: str):
        raise NotImplementedError("Real 17TRACK integration not implemented yet")