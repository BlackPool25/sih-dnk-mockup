"""Mock penny-drop provider stub."""

from __future__ import annotations


def mock_penny_drop(account_number: str, ifsc: str, amount_minor: int = 100) -> dict[str, object]:
    """Mocked penny-drop (₹1) verification."""
    _ = (account_number, ifsc, amount_minor)
    return {
        "status": "success",
        "penny_status": "credited",
        "amount_minor": amount_minor,
        "mocked": True,
        "provider": "mock_penny",
        "verification_mode": "mock",
    }
