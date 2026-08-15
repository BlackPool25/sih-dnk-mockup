from abc import ABC, abstractmethod
from typing import Optional, Dict

class TrackingProvider(ABC):
    @abstractmethod
    def get_next_status(self, current_status: str) -> Optional[Dict[str, str]]:
        pass