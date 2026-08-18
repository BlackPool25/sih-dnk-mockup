import os
import httpx
from .base import TrackingProvider

TRACK17_BASE_URL = "https://api.17track.net/track/v2.4"

CARRIER_CODES = {
    "IndiaPost": 9021,  # confirmed via live carrier list
}

# Maps 17TRACK's 9 real main statuses to your own vocabulary
STATUS_MAP = {
    "NotFound": "Booked",  # not yet picked up / no carrier scan yet
    "InfoReceived": "Booked",
    "InTransit": "In Transit",
    "AvailableForPickup": "Out for Delivery",
    "OutForDelivery": "Out for Delivery",
    "DeliveryFailure": "Exception",
    "Delivered": "Delivered",
    "Expired": "Exception",
    "Exception": "Exception",
}


class RealProvider(TrackingProvider):
    def __init__(self):
        self.api_key = os.getenv("TRACK17_API_KEY")
        if not self.api_key:
            raise RuntimeError("TRACK17_API_KEY not set")
        self.headers = {
            "17token": self.api_key,
            "Content-Type": "application/json",
        }

    def register(self, tracking_number: str, carrier: str) -> None:
        carrier_code = CARRIER_CODES.get(carrier)
        if carrier_code is None:
            raise ValueError(f"Unknown carrier: {carrier}")

        payload = [{"number": tracking_number, "carrier": carrier_code}]
        response = httpx.post(
            f"{TRACK17_BASE_URL}/register",
            headers=self.headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if data["data"]["rejected"]:
            reason = data["data"]["rejected"][0]["error"]["message"]
            raise RuntimeError(f"17TRACK rejected registration: {reason}")

    def get_latest_status(self, tracking_number: str, current_status: str):
        payload = [{"number": tracking_number}]
        response = httpx.post(
            f"{TRACK17_BASE_URL}/gettrackinfo",
            headers=self.headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        accepted = data.get("data", {}).get("accepted", [])
        if not accepted:
            return None  # not found or not yet synced

        track_info = accepted[0]["track_info"]
        raw_status = track_info["latest_status"]["status"]
        mapped_status = STATUS_MAP.get(raw_status)

        if mapped_status is None or mapped_status == current_status:
            return None  # nothing new to report

        # Location comes from the most recent event, if any exist yet
        location = "Unknown"
        providers = track_info.get("tracking", {}).get("providers", [])
        if providers:
            events = providers[0].get("events", [])
            if events:
                location = events[0].get("location") or "Unknown"

        return {"status": mapped_status, "location": location}