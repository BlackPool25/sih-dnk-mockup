"""Profile CRUD routes — create, read, update seller profiles.

All endpoints require seller authentication.  Sensitive fields (pan,
bank_account, ad_code, gstin) are encrypted before storage and decrypted
before being returned to the client via ``profile_crypto``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.models.profile import SellerProfile
from app.schemas.profile import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.services.profile_crypto import (
    ENCRYPTED_FIELDS,
    decrypt_profile_fields,
    encrypt_profile_fields,
)
from auth.deps import get_current_user, require_role
from storage.db import get_session

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/profile", tags=["profile"])

# ---------------------------------------------------------------------------
# Field mapping — plain API names ↔ PostgreSQL column names
# ---------------------------------------------------------------------------

_PLAIN_TO_MODEL: dict[str, str] = {
    "pan": "pan_encrypted",
    "bank_account": "bank_account_encrypted",
    "ad_code": "ad_code_encrypted",
    "gstin": "gstin_encrypted",
}

_MODEL_TO_PLAIN: dict[str, str] = {v: k for k, v in _PLAIN_TO_MODEL.items()}

# Model columns for simple (non-encrypted) fields that map 1:1 to API names
_SIMPLE_FIELDS: list[str] = [
    "firm_name",
    "owner_name",
    "bank_name",
    "ifsc",
    "bank_branch",
    "iec",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "pincode",
    "phone",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_encrypted(model_instance: SellerProfile) -> dict[str, object]:
    """Extract encrypted column values from a profile instance, mapped to
    plain field names expected by ``decrypt_profile_fields``.

    Skips fields whose value is ``None`` (never stored).
    """
    crypto_dict: dict[str, object] = {}
    for model_col, plain_field in _MODEL_TO_PLAIN.items():
        value = getattr(model_instance, model_col, None)
        if value is not None:
            crypto_dict[plain_field] = value
    return crypto_dict


def _build_response(profile: SellerProfile, plain: dict[str, object]) -> dict[str, object]:
    """Assemble a dict suitable for ``ProfileResponse``."""
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "firm_name": profile.firm_name,
        "owner_name": profile.owner_name,
        "pan": plain.get("pan"),
        "bank_name": profile.bank_name,
        "bank_account": plain.get("bank_account"),
        "ifsc": profile.ifsc,
        "bank_branch": profile.bank_branch,
        "iec": profile.iec,
        "ad_code": plain.get("ad_code"),
        "gstin": plain.get("gstin"),
        "address_line1": profile.address_line1,
        "address_line2": profile.address_line2,
        "city": profile.city,
        "state": profile.state,
        "pincode": profile.pincode,
        "phone": profile.phone,
        "is_verified": profile.is_verified,
        "profile_version": profile.profile_version,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /profile — Create
# ---------------------------------------------------------------------------


@router.post(
    "",
    status_code=201,
    response_model=ProfileResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def create_profile(
    request: Request,
    body: ProfileCreateRequest,
) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])

    # Check for duplicate profile
    async with get_session()() as session:
        existing = await session.execute(
            select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id))
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Profile already exists for this user",
            )

    profile_data = body.model_dump()

    # Separate sensitive fields → encrypt them
    crypto_dict: dict[str, str | None] = {}
    for field in ENCRYPTED_FIELDS:
        value = profile_data.pop(field, None)
        if value is not None:
            crypto_dict[field] = value

    encrypt_profile_fields(crypto_dict, user_id)

    # Build model column data
    model_kwargs: dict[str, object] = {"user_id": uuid.UUID(user_id)}
    for field in _SIMPLE_FIELDS:
        if field in profile_data:
            model_kwargs[field] = profile_data[field]
    for plain_field, encrypted_value in crypto_dict.items():
        model_kwargs[_PLAIN_TO_MODEL[plain_field]] = encrypted_value

    async with get_session()() as session:
        profile = SellerProfile(**model_kwargs)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        crypto_dict = _extract_encrypted(profile)
        decrypt_profile_fields(crypto_dict, user_id)
        return _build_response(profile, crypto_dict)


# ---------------------------------------------------------------------------
# GET /profile — Read
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ProfileResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def get_profile(request: Request) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])

    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id))
        )
        profile = result.scalar_one_or_none()

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        crypto_dict = _extract_encrypted(profile)
        decrypt_profile_fields(crypto_dict, user_id)
        return _build_response(profile, crypto_dict)


# ---------------------------------------------------------------------------
# PUT /profile — Update (partial)
# ---------------------------------------------------------------------------


@router.put(
    "",
    response_model=ProfileResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def update_profile(
    request: Request,
    body: ProfileUpdateRequest,
) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id))
        )
        profile = result.scalar_one_or_none()

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Split updates into simple fields and encrypted fields
        crypto_updates: dict[str, str | None] = {}
        for field_name, value in update_data.items():
            if field_name in _PLAIN_TO_MODEL:
                crypto_updates[field_name] = value
            elif field_name in _SIMPLE_FIELDS:
                setattr(profile, field_name, value)

        # Encrypt changed sensitive fields
        if crypto_updates:
            encrypt_profile_fields(crypto_updates, user_id)
            for plain_field, encrypted_value in crypto_updates.items():
                model_col = _PLAIN_TO_MODEL[plain_field]
                setattr(profile, model_col, encrypted_value)

        # Bump version
        profile.profile_version += 1

        await session.commit()
        await session.refresh(profile)

        crypto_dict = _extract_encrypted(profile)
        decrypt_profile_fields(crypto_dict, user_id)
        return _build_response(profile, crypto_dict)
