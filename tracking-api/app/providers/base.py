from abc import ABC, abstractmethod
from typing import Optional, Dict

class TrackingProvider(ABC):
    @abstractmethod
    def register(self, tracking_number: str, carrier: str) -> None:
        """Register a tracking number with the provider. No-op for mock."""
        pass

    @abstractmethod
    def get_latest_status(self, tracking_number: str, current_status: str) -> Optional[Dict[str, str]]:
        """
        Returns {"status": ..., "location": ...} if there's a NEW status
        since current_status, otherwise None (nothing changed).
        """
        pass