"""Profile CRUD routes — create, read, update seller profiles.

All endpoints require seller authentication.  Sensitive fields (pan,
bank_account, ad_code, gstin) are encrypted before storage and decrypted
before being returned to the client via ``profile_crypto``.

Hardening:
- PUT re-validates pan/ifsc/iec/pincode/phone/gstin/ad_code regex (via schemas)
- is_verified only true when trust_level L2 (IEC+AD+bank+IFSC present)
- payouts_frozen + vernacular hard block on AD/bank mismatch
- buyer foreign minimal mock (no PAN) via POST /profile/buyer
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.models.profile import SellerProfile
from app.schemas.profile import (
    BuyerProfileRequest,
    BuyerProfileResponse,
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    SahayakProfileRequest,
    SahayakProfileResponse,
)
from app.services.profile_crypto import (
    ENCRYPTED_FIELDS,
    decrypt_profile_fields,
    encrypt_profile_fields,
)
from auth.deps import get_current_user, require_role
from storage.db import get_session

router = APIRouter(prefix="/profile", tags=["profile"])

_PLAIN_TO_MODEL: dict[str, str] = {
    "pan": "pan_encrypted",
    "bank_account": "bank_account_encrypted",
    "ad_code": "ad_code_encrypted",
    "gstin": "gstin_encrypted",
}

_MODEL_TO_PLAIN: dict[str, str] = {v: k for k, v in _PLAIN_TO_MODEL.items()}

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

_PAYOUTS_FROZEN: dict[str, bool] = {}
_BINDING_SNAPSHOT: dict[str, dict[str, str | None]] = {}

_VERNACULAR_BLOCK = "यह खाता आपके IEC से लिंक AD Code के खाते से मेल नहीं खाता — इससे आपकी e-BRC नहीं बनेगी"

def _extract_encrypted(model_instance: SellerProfile) -> dict[str, object]:
    crypto_dict: dict[str, object] = {}
    for model_col, plain_field in _MODEL_TO_PLAIN.items():
        value = getattr(model_instance, model_col, None)
        if value is not None:
            crypto_dict[plain_field] = value
    return crypto_dict

def _compute_trust(iec: str | None, ad_code: str | None, ifsc: str | None, bank_account: str | None, pan: str | None) -> tuple[str, int, bool]:
    if iec and ad_code and ifsc and bank_account:
        return "L2", 85, True
    if pan:
        return "L1", 50, False
    return "L0", 25, False

def _build_response(profile: SellerProfile, plain: dict[str, object]) -> dict[str, object]:
    pan = plain.get("pan") if isinstance(plain.get("pan"), str) else None
    ad_code = plain.get("ad_code") if isinstance(plain.get("ad_code"), str) else None
    bank_account = plain.get("bank_account") if isinstance(plain.get("bank_account"), str) else None
    trust_level, trust_score, is_verified = _compute_trust(profile.iec, ad_code, profile.ifsc, bank_account, pan)
    user_key = str(profile.user_id)
    payouts_frozen = _PAYOUTS_FROZEN.get(user_key, False)
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "firm_name": profile.firm_name,
        "owner_name": profile.owner_name,
        "pan": pan,
        "bank_name": profile.bank_name,
        "bank_account": bank_account,
        "ifsc": profile.ifsc,
        "bank_branch": profile.bank_branch,
        "iec": profile.iec,
        "ad_code": ad_code,
        "gstin": plain.get("gstin"),
        "address_line1": profile.address_line1,
        "address_line2": profile.address_line2,
        "city": profile.city,
        "state": profile.state,
        "pincode": profile.pincode,
        "phone": profile.phone,
        "is_verified": is_verified and not payouts_frozen,
        "trust_level": trust_level,
        "trust_score": trust_score,
        "payouts_frozen": payouts_frozen,
        "profile_version": profile.profile_version,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
        "verification_mode": "mock",
        "mocked": True,
    }

def _detect_hard_block(existing_ad: str | None, existing_ifsc: str | None, proposed_ad: str | None, proposed_ifsc: str | None) -> tuple[bool, dict[str, str | None]]:
    side_by_side: dict[str, str | None] = {"current_ad": existing_ad,"proposed_ad": proposed_ad,"current_ifsc": existing_ifsc,"proposed_ifsc": proposed_ifsc,"current_bank": existing_ifsc[:4] if existing_ifsc else None,"proposed_bank": proposed_ifsc[:4] if proposed_ifsc else None}
    if existing_ad is None or existing_ifsc is None:
        return False, side_by_side
    if proposed_ad is None and proposed_ifsc is None:
        return False, side_by_side
    ad_mismatch = proposed_ad is not None and proposed_ad != existing_ad
    bank_mismatch = (proposed_ifsc is not None and existing_ifsc is not None and proposed_ifsc[:4] != existing_ifsc[:4])
    return (ad_mismatch or bank_mismatch), side_by_side

@router.post("", status_code=201, response_model=ProfileResponse, dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def create_profile(request: Request, body: ProfileCreateRequest) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    async with get_session()() as session:
        existing = await session.execute(select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id)))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Profile already exists for this user")
    profile_data = body.model_dump()
    crypto_dict: dict[str, object] = {}
    for field in ENCRYPTED_FIELDS:
        value = profile_data.pop(field, None)
        if value is not None:
            crypto_dict[field] = value
    encrypt_profile_fields(crypto_dict, user_id)
    model_kwargs: dict[str, object] = {"user_id": uuid.UUID(user_id)}
    for field in _SIMPLE_FIELDS:
        if field in profile_data:
            model_kwargs[field] = profile_data[field]
    for plain_field, encrypted_value in crypto_dict.items():
        model_kwargs[_PLAIN_TO_MODEL[plain_field]] = encrypted_value
    pan_plain = body.pan
    ad_plain = body.ad_code
    iec_plain = body.iec
    ifsc_plain = body.ifsc
    bank_plain = body.bank_account
    _tl, _ts, is_verified_flag = _compute_trust(iec_plain, ad_plain, ifsc_plain, bank_plain, pan_plain)
    model_kwargs["is_verified"] = is_verified_flag
    async with get_session()() as session:
        profile = SellerProfile(**model_kwargs)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        _BINDING_SNAPSHOT[user_id] = {"ad_code": ad_plain, "ifsc": ifsc_plain}
        crypto_dict_out = _extract_encrypted(profile)
        decrypt_profile_fields(crypto_dict_out, user_id)
        return _build_response(profile, crypto_dict_out)

@router.get("", response_model=ProfileResponse, dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def get_profile(request: Request) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    async with get_session()() as session:
        result = await session.execute(select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id)))
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        crypto_dict = _extract_encrypted(profile)
        decrypt_profile_fields(crypto_dict, user_id)
        return _build_response(profile, crypto_dict)

@router.put("", response_model=ProfileResponse, dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def update_profile(request: Request, body: ProfileUpdateRequest) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    async with get_session()() as session:
        result = await session.execute(select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id)))
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        existing_crypto = _extract_encrypted(profile)
        decrypt_profile_fields(existing_crypto, user_id)
        existing_ad: str | None = existing_crypto.get("ad_code") if isinstance(existing_crypto.get("ad_code"), str) else None
        existing_ifsc: str | None = profile.ifsc
        snap = _BINDING_SNAPSHOT.get(user_id)
        if snap is not None:
            existing_ad = snap.get("ad_code") or existing_ad
            existing_ifsc = snap.get("ifsc") or existing_ifsc
        proposed_ad: str | None = update_data.get("ad_code") if isinstance(update_data.get("ad_code"), str) else None
        proposed_ifsc: str | None = update_data.get("ifsc") if isinstance(update_data.get("ifsc"), str) else None
        mismatched, side_by_side = _detect_hard_block(existing_ad, existing_ifsc, proposed_ad, proposed_ifsc)
        if mismatched:
            _PAYOUTS_FROZEN[user_id] = True
            raise HTTPException(status_code=422, detail={"message": _VERNACULAR_BLOCK,"vernacular": _VERNACULAR_BLOCK,"side_by_side": side_by_side,"payouts_frozen": True,"reason": "AD/bank mismatch — e-BRC will fail"})
        if _PAYOUTS_FROZEN.get(user_id) and (proposed_ad is not None or proposed_ifsc is not None):
            raise HTTPException(status_code=422, detail={"message": _VERNACULAR_BLOCK,"vernacular": _VERNACULAR_BLOCK,"side_by_side": side_by_side,"payouts_frozen": True,"reason": "payouts frozen — human gate required"})
        crypto_updates: dict[str, object] = {}
        for field_name, value in update_data.items():
            if field_name in _PLAIN_TO_MODEL:
                crypto_updates[field_name] = value
            elif field_name in _SIMPLE_FIELDS:
                setattr(profile, field_name, value)
        if crypto_updates:
            encrypt_profile_fields(crypto_updates, user_id)
            for plain_field, encrypted_value in crypto_updates.items():
                model_col = _PLAIN_TO_MODEL[plain_field]
                setattr(profile, model_col, encrypted_value)
        final_crypto: dict[str, object] = dict(existing_crypto)
        for k, v in crypto_updates.items():
            plain_val = update_data.get(k)
            if plain_val is not None:
                final_crypto[k] = plain_val
        final_ad = final_crypto.get("ad_code") if isinstance(final_crypto.get("ad_code"), str) else None
        final_pan = final_crypto.get("pan") if isinstance(final_crypto.get("pan"), str) else None
        final_bank = final_crypto.get("bank_account") if isinstance(final_crypto.get("bank_account"), str) else None
        final_iec = profile.iec
        final_ifsc = profile.ifsc
        _tl, _ts, is_verified_new = _compute_trust(final_iec, final_ad, final_ifsc, final_bank, final_pan)
        profile.is_verified = is_verified_new and not _PAYOUTS_FROZEN.get(user_id, False)
        profile.profile_version += 1
        await session.commit()
        await session.refresh(profile)
        if proposed_ad is not None or proposed_ifsc is not None:
            snap = _BINDING_SNAPSHOT.get(user_id, {})
            if proposed_ad is not None:
                snap["ad_code"] = proposed_ad
            if proposed_ifsc is not None:
                snap["ifsc"] = proposed_ifsc
            _BINDING_SNAPSHOT[user_id] = snap
        crypto_dict = _extract_encrypted(profile)
        decrypt_profile_fields(crypto_dict, user_id)
        return _build_response(profile, crypto_dict)

_SAHAYAK_ALLOWLIST: set[str] = {"DNK-BLR-01", "DNK-DEL-01", "DNK-MUM-01", "DNK-DEL-02"}

@router.post("/buyer", status_code=201, dependencies=[Depends(get_current_user)])
async def create_buyer_profile(request: Request, body: BuyerProfileRequest) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    country_upper = body.country.upper() if body.country else None
    return {"buyer_id": user_id,"name": body.name,"email": body.email or request.state.user.get("email"),"country": country_upper,"phone": body.phone,"address": body.address,"passport_mock": bool(body.passport_mock),"mocked": True,"verification_mode": "mock","pan_required": False,"note": "foreign buyer — no PAN verification","is_verified": True,"trust_level": "L0","trust_score": 25,"payouts_frozen": False,"provider": "mock_cashfree"}

@router.get("/buyer", dependencies=[Depends(get_current_user)])
async def get_buyer_profile(request: Request) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    return {"buyer_id": user_id,"name": request.state.user.get("email", "buyer"),"email": request.state.user.get("email"),"country": None,"phone": None,"mocked": True,"verification_mode": "mock","pan_required": False,"note": "foreign buyer — no PAN verification","is_verified": True,"trust_level": "L0"}

@router.post("/sahayak", status_code=201, response_model=SahayakProfileResponse, dependencies=[Depends(get_current_user)])
async def create_sahayak_profile(request: Request, body: SahayakProfileRequest) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    if body.center_code not in _SAHAYAK_ALLOWLIST:
        raise HTTPException(status_code=403, detail=f"center_code not in allowlist {sorted(_SAHAYAK_ALLOWLIST)}")
    return {"sahayak_id": user_id,"center_code": body.center_code,"employee_id": body.employee_id,"email": body.email,"phone": body.phone,"mocked": True,"verification_mode": "mock","is_verified": True,"trust_level": "L0","trust_score": 25,"note": "sahayak allowlist verified (mock)"}

@router.get("/sahayak", dependencies=[Depends(get_current_user)])
async def get_sahayak_profile(request: Request) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    return {"sahayak_id": user_id,"mocked": True,"verification_mode": "mock","is_verified": False,"trust_level": "L0","note": "sahayak allowlist verified (mock)", "allowlist": sorted(_SAHAYAK_ALLOWLIST)}

@router.post("/bindings/confirm-human-gate", dependencies=[Depends(get_current_user), Depends(require_role("seller"))])
async def confirm_human_gate_profile(request: Request, body: dict) -> dict[str, object]:
    user_id: str = str(request.state.user["user_id"])
    current_ad = body.get("current_ad") or body.get("current_ad_code")
    proposed_ad = body.get("proposed_ad") or body.get("proposed_ad_code") or current_ad
    current_ifsc = body.get("current_ifsc")
    proposed_ifsc = body.get("proposed_ifsc")
    if not current_ad or not proposed_ad:
        raise HTTPException(status_code=422, detail="current_ad and proposed_ad required (14 digits)")
    side_by_side = {"current_ad": current_ad,"proposed_ad": proposed_ad,"current_ifsc": current_ifsc,"proposed_ifsc": proposed_ifsc,"current_bank": current_ifsc[:4] if isinstance(current_ifsc, str) else None,"proposed_bank": proposed_ifsc[:4] if isinstance(proposed_ifsc, str) else None}
    if _PAYOUTS_FROZEN.get(user_id):
        _PAYOUTS_FROZEN[user_id] = False
        _BINDING_SNAPSHOT[user_id] = {"ad_code": str(proposed_ad), "ifsc": proposed_ifsc}
    else:
        _BINDING_SNAPSHOT[user_id] = {"ad_code": str(proposed_ad), "ifsc": proposed_ifsc}
    return {"user_id": user_id,"human_gate_confirmed": True,"side_by_side": side_by_side,"payouts_frozen": False,"mocked": True,"verification_mode": "mock","provider_request_id": f"mocked-{uuid.uuid4().hex[:12]}"}
