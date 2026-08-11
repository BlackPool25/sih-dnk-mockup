"""Document upload/download routes — encrypted KYC document storage.

All endpoints require seller authentication.  File contents are encrypted
with AES-256-GCM before storage and decrypted on download with SHA-256
integrity verification.
"""

from __future__ import annotations

import base64
import hashlib
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import select

from app.models.profile import SellerProfile
from app.models.profile_document import DocumentType, ProfileDocument
from auth.deps import get_current_user, require_role
from storage.config import settings
from storage.crypto import DecryptionError, decrypt_field, encrypt_field
from storage.db import get_session

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/profile/documents", tags=["documents"])

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_KEY_VERSION = 1


def _get_master_key() -> bytes:
    """Hex-decode the master key from settings (64-char hex → 32 bytes)."""
    return bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)


# ---------------------------------------------------------------------------
# POST /profile/documents — Upload
# ---------------------------------------------------------------------------


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
    doc_type: DocumentType = Form(...),  # noqa: B008
) -> dict[str, str]:
    """Upload an encrypted KYC document for the authenticated seller's profile.

    File is read into memory, SHA-256 checksummed, base64-encoded, encrypted
    with AES-256-GCM, and stored in the ``profile_documents`` table.
    Returns metadata only — never the encrypted content.
    """
    user_id: str = str(request.state.user["user_id"])

    # Read and validate
    content: bytes = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds maximum allowed size of 10 MB",
        )

    # Compute SHA-256 checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Base64-encode for encryption (encrypt_field operates on strings)
    b64_content = base64.b64encode(content).decode("ascii")

    # Encrypt with AES-256-GCM
    encrypted = encrypt_field(b64_content, user_id, _get_master_key(), _KEY_VERSION)

    async with get_session()() as session:
        # Resolve user's seller profile
        result = await session.execute(
            select(SellerProfile).where(
                SellerProfile.user_id == uuid.UUID(user_id),
            ),
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        doc = ProfileDocument(
            profile_id=profile.id,
            doc_type=doc_type,
            filename=file.filename or "unnamed",
            mime_type=file.content_type or "application/octet-stream",
            encrypted_content=encrypted,
            checksum_sha256=checksum,
            key_version=_KEY_VERSION,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        return {
            "id": str(doc.id),
            "doc_type": doc.doc_type.value,
            "filename": doc.filename,
            "checksum_sha256": doc.checksum_sha256,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# GET /profile/documents — List
# ---------------------------------------------------------------------------


@router.get(
    "",
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def list_documents(request: Request) -> list[dict[str, str]]:
    """List all documents for the authenticated seller's profile."""
    user_id: str = str(request.state.user["user_id"])

    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(
                SellerProfile.user_id == uuid.UUID(user_id),
            ),
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        result = await session.execute(
            select(ProfileDocument)
            .where(ProfileDocument.profile_id == profile.id)
            .order_by(ProfileDocument.uploaded_at.desc()),
        )
        docs = result.scalars().all()

        return [
            {
                "id": str(doc.id),
                "doc_type": doc.doc_type.value,
                "filename": doc.filename,
                "mime_type": doc.mime_type,
                "checksum_sha256": doc.checksum_sha256,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
            for doc in docs
        ]


# ---------------------------------------------------------------------------
# GET /profile/documents/{doc_id} — Download
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}",
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def download_document(request: Request, doc_id: str) -> Response:
    """Download a previously uploaded document.

    Decrypts the stored content, verifies the SHA-256 checksum against the
    database record, and returns the original bytes with the correct MIME type.
    """
    user_id: str = str(request.state.user["user_id"])

    # Parse UUID
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    async with get_session()() as session:
        # Resolve profile
        profile_result = await session.execute(
            select(SellerProfile).where(
                SellerProfile.user_id == uuid.UUID(user_id),
            ),
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Fetch document
        doc_result = await session.execute(
            select(ProfileDocument).where(ProfileDocument.id == doc_uuid),
        )
        doc = doc_result.scalar_one_or_none()

        if doc is None or doc.profile_id != profile.id:
            raise HTTPException(status_code=404, detail="Document not found")

        # Decrypt
        try:
            plaintext = decrypt_field(doc.encrypted_content, user_id, _get_master_key())
        except DecryptionError:
            raise HTTPException(
                status_code=500,
                detail="Decryption failed: wrong key or corrupted data",
            )

        # Decode base64 → original bytes
        content = base64.b64decode(plaintext)

        # Verify checksum
        actual_checksum = hashlib.sha256(content).hexdigest()
        if actual_checksum != doc.checksum_sha256:
            raise HTTPException(
                status_code=500,
                detail="Checksum verification failed: file may be corrupted",
            )

        return Response(
            content=content,
            media_type=doc.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{doc.filename}"',
            },
        )
