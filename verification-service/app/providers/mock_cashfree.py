"""Mock Cashfree provider — PAN + bank verification stubs."""

from __future__ import annotations


def mock_pan_verify(pan: str) -> dict[str, object]:
    """Mocked PAN verification — deterministic success for demo."""
    _ = pan
    return {
        "status": "success",
        "pan_status": "valid",
        "name_match": True,
        "mocked": True,
        "provider": "mock_cashfree",
        "verification_mode": "mock",
    }


def mock_bank_verify(account_number: str, ifsc: str) -> dict[str, object]:
    """Mocked bank account verification."""
    _ = (account_number, ifsc)
    return {
        "status": "success",
        "account_status": "valid",
        "name_match": True,
        "mocked": True,
        "provider": "mock_cashfree",
        "verification_mode": "mock",
    }
