import random
from .base import TrackingProvider

STATE_FLOW = ["Booked", "Picked Up", "In Transit", "Out for Delivery", "Delivered"]

LOCATIONS = {
    "Picked Up": ["Pune Hub", "Mumbai Hub", "Delhi Hub"],
    "In Transit": ["Mumbai Transit Center", "Dubai Transit Hub", "Frankfurt Transit Hub"],
    "Out for Delivery": ["Local Delivery Center"],
    "Delivered": ["Destination Address"],
}

class MockProvider(TrackingProvider):
    def register(self, tracking_number: str, carrier: str) -> None:
        pass  # nothing to register, mock generates its own progression

    def get_latest_status(self, tracking_number: str, current_status: str):
        if current_status not in STATE_FLOW:
            return None
        current_index = STATE_FLOW.index(current_status)
        next_index = current_index + 1
        if next_index >= len(STATE_FLOW):
            return None
        next_status = STATE_FLOW[next_index]
        location = random.choice(LOCATIONS.get(next_status, ["Unknown"]))
        return {"status": next_status, "location": location}