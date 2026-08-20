"""Mock DigiLocker provider stub."""
from __future__ import annotations
import uuid
def _mocked_id() -> str:
    return f"mocked-{uuid.uuid4().hex[:12]}"
def mock_digilocker_verify(document_type: str, document_number: str) -> dict[str, object]:
    _ = (document_type, document_number)
    return {"status": "success","document_status": "valid","mocked": True,"provider": "mock_digilocker","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False}
def mock_digilocker_pan_aadhaar(pan: str, aadhaar: str) -> dict[str, object]:
    _ = (pan, aadhaar)
    return {"status": "success","pan_status": "valid","aadhaar_status": "valid","mocked": True,"provider": "mock_digilocker","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False,"note": "DigiLocker mock — PAN+Aadhaar via mocked gateway"}
