"""Mock penny-drop provider stub — reverse UPI 10min validUpto."""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
def _mocked_id() -> str:
    return f"mocked-{uuid.uuid4().hex[:12]}"
def _valid_upto() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
def mock_penny_drop(account_number: str, ifsc: str, amount_minor: int = 100) -> dict[str, object]:
    _ = (account_number, ifsc, amount_minor)
    return {"status": "success","penny_status": "credited","amount_minor": amount_minor,"mocked": True,"provider": "mock_penny","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False,"reverse_penny": {"upi": f"mock-upi-{account_number[-4:]}@mock","amount_minor": 100,"validUpto": _valid_upto()},"reverse_upi": f"mock-upi-{account_number[-4:]}@mock","validUpto": _valid_upto()}
def mock_iec_view(iec: str) -> dict[str, object]:
    return {"status": "success","iec": iec,"iec_status": "valid","mocked": True,"provider": "mock_iec_view_any","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False,"note": "DGFT View Any IEC mocked"}
