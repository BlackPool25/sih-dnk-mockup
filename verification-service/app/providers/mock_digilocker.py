"""Mock DigiLocker provider stub."""

from __future__ import annotations


def mock_digilocker_verify(document_type: str, document_number: str) -> dict[str, object]:
    """Mocked DigiLocker verification."""
    _ = (document_type, document_number)
    return {
        "status": "success",
        "document_status": "valid",
        "mocked": True,
        "provider": "mock_digilocker",
        "verification_mode": "mock",
    }
