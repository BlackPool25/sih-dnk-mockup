"""Tests for profile document upload/download routes."""

from __future__ import annotations

import hashlib

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

SELLER_PROFILE_PAYLOAD: dict[str, str] = {
    "firm_name": "Test Exports Ltd",
    "owner_name": "John Doe",
    "pan": "ABCDE1234F",
    "bank_name": "State Bank of India",
    "bank_account": "12345678901",
    "ifsc": "SBIN0001234",
    "bank_branch": "Mumbai Main",
    "iec": "1234567890",
    "ad_code": "12345678901234",
    "gstin": "22AAAAA0000A1Z5",
    "address_line1": "123 Shipping Lane",
    "address_line2": "Andheri East",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400069",
    "phone": "9876543210",
}

PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_profile(client: AsyncClient, token: str) -> None:
    """Create a seller profile via the API (prerequisite for document ops)."""
    resp = await client.post(
        "/profile",
        json=SELLER_PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_document(test_seller: dict[str, str]) -> None:
    """Upload a PDF → 201 with metadata (no encrypted content exposed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        response = await client.post(
            "/profile/documents",
            files={"file": ("pan_card.pdf", PDF_BYTES, "application/pdf")},
            data={"doc_type": "pan_card"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["doc_type"] == "pan_card"
    assert data["filename"] == "pan_card.pdf"
    assert "checksum_sha256" in data
    assert len(data["checksum_sha256"]) == 64
    assert "id" in data
    assert "uploaded_at" in data
    # Must NOT expose encrypted content
    assert "encrypted_content" not in data
    assert "ciphertext_b64" not in data


@pytest.mark.asyncio
async def test_upload_too_large(test_seller: dict[str, str]) -> None:
    """Upload >10MB → 413 Payload Too Large."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        large = b"A" * (10 * 1024 * 1024 + 1)  # 10 MB + 1 byte
        response = await client.post(
            "/profile/documents",
            files={"file": ("large.bin", large, "application/octet-stream")},
            data={"doc_type": "other"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 413
    assert "10 MB" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_documents(test_seller: dict[str, str]) -> None:
    """Upload a document then list — should appear in results."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        # Upload one
        upload_resp = await client.post(
            "/profile/documents",
            files={"file": ("gst.pdf", PDF_BYTES, "application/pdf")},
            data={"doc_type": "gst_certificate"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert upload_resp.status_code == 201
        doc_id = upload_resp.json()["id"]

        # List
        list_resp = await client.get(
            "/profile/documents",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) >= 1
    found = [d for d in docs if d["id"] == doc_id]
    assert len(found) == 1
    assert found[0]["doc_type"] == "gst_certificate"
    assert found[0]["filename"] == "gst.pdf"
    assert "mime_type" in found[0]
    assert "checksum_sha256" in found[0]
    assert "uploaded_at" in found[0]


@pytest.mark.asyncio
async def test_download_and_verify(test_seller: dict[str, str]) -> None:
    """Download a document → original bytes + SHA-256 match."""
    original_content = PDF_BYTES
    expected_checksum = hashlib.sha256(original_content).hexdigest()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        # Upload
        upload_resp = await client.post(
            "/profile/documents",
            files={"file": ("iec_cert.pdf", original_content, "application/pdf")},
            data={"doc_type": "iec_certificate"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert upload_resp.status_code == 201
        doc_id = upload_resp.json()["id"]
        assert upload_resp.json()["checksum_sha256"] == expected_checksum

        # Download
        download_resp = await client.get(
            f"/profile/documents/{doc_id}",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert download_resp.status_code == 200
    assert download_resp.content == original_content
    assert download_resp.headers["content-type"] == "application/pdf"
    assert "attachment" in download_resp.headers["content-disposition"]
    assert "iec_cert.pdf" in download_resp.headers["content-disposition"]

    # Verify SHA-256 of downloaded bytes
    actual_checksum = hashlib.sha256(download_resp.content).hexdigest()
    assert actual_checksum == expected_checksum


@pytest.mark.asyncio
async def test_unauthorized() -> None:
    """No auth token → 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/profile/documents",
            files={"file": ("test.pdf", PDF_BYTES, "application/pdf")},
            data={"doc_type": "pan_card"},
        )

    assert response.status_code == 401
