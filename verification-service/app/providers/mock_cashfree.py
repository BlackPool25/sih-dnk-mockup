"""Mock Cashfree provider — PAN + bank verification stubs (MOCK_VERIFICATION=true)."""

from __future__ import annotations

import os
import uuid


def _mocked_id() -> str:
    return f"mocked-{uuid.uuid4().hex[:12]}"


MOCK_VERIFICATION: bool = os.getenv("MOCK_VERIFICATION", "true").lower() in ("1", "true", "yes")


def mock_pan_verify(pan: str) -> dict[str, object]:
    _ = pan
    return {"status": "success","pan_status": "valid","name_match": True,"mocked": True,"provider": "mock_cashfree","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False,"note": "mocked demo — never claim live"}

def mock_bank_verify(account_number: str, ifsc: str) -> dict[str, object]:
    _ = (account_number, ifsc)
    return {"status": "success","account_status": "valid","name_match": True,"mocked": True,"provider": "mock_cashfree","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False,"note": "mocked demo — never claim live"}

def mock_cashfree_bundle(pan: str | None = None, account_number: str | None = None, ifsc: str | None = None, seller_id: str | None = None) -> dict[str, object]:
    _ = (pan, account_number, ifsc, seller_id)
    return {"status": "success","bundle": "secure_id","pan_status": "valid" if pan else None,"account_status": "valid" if account_number and ifsc else None,"mocked": True,"provider": "mock_cashfree_bundle","provider_request_id": _mocked_id(),"verification_mode": "mock","live_claim": False,"mock_verification": True,"note": "Cashfree bundle mocked — MOCK_VERIFICATION=true, never live","attempts_stored": True}
