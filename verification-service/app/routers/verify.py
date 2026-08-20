"""Verification router — L0→L3 mocked endpoints + trust + bindings + Cashfree bundle."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.providers.mock_cashfree import mock_cashfree_bundle
from app.state import confirm_human_gate, get_trust, mock_buyer, mock_l0, mock_l1, mock_l2, mock_liveness, mock_sahayak, mock_verify
from app.state import VerificationLevel

router = APIRouter(prefix="/verify", tags=["verify"])
trust_router = APIRouter(tags=["trust"])
bindings_router = APIRouter(prefix="/bindings", tags=["bindings"])

# ---------------------------------------------------------------------------
# Explicit L0 / L1 / L2 / Liveness — spec compliant (must be BEFORE generic)
# ---------------------------------------------------------------------------

class L0Request(BaseModel):
    phone: str = Field(..., description="10-digit Indian mobile")
    seller_id: str | None = None
    user_id: str | None = None

class L1Request(BaseModel):
    pan: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    aadhaar: str = Field(..., pattern=r"^\d{12}$")
    seller_id: str | None = None
    user_id: str | None = None

class L2Request(BaseModel):
    iec: str = Field(..., pattern=r"^\d{10}$")
    ad_code: str = Field(..., pattern=r"^\d{14}$")
    bank_account: str | None = Field(None, description="bank account number")
    account_number: str | None = None
    ifsc: str = Field(..., pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    penny: bool | None = True
    seller_id: str | None = None
    user_id: str | None = None

class LivenessRequest(BaseModel):
    selfie: str | None = Field(None, description="base64 selfie mocked")
    image: str | None = None
    seller_id: str | None = None
    user_id: str | None = None

def _resolve_seller_id(*candidates: str | None) -> str:
    for c in candidates:
        if c and c.strip():
            return c.strip()
    return f"anon-{uuid.uuid4().hex[:8]}"

@router.post("/l0")
async def verify_l0(body: L0Request) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    result = mock_l0(body.phone, sid)
    if result.get("status") == "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=result.get("error", "invalid phone"))
    return result

@router.post("/l1")
async def verify_l1(body: L1Request) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    result = mock_l1(body.pan, body.aadhaar, sid)
    if result.get("status") == "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=result.get("error", "validation failed"))
    return result

@router.post("/l2")
async def verify_l2(body: L2Request) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    acct = body.bank_account or body.account_number or "0000000000"
    result = mock_l2(body.iec, body.ad_code, acct, body.ifsc, sid)
    if result.get("status") == "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=result.get("error", "validation failed"))
    return result

@router.post("/liveness")
async def verify_liveness(body: LivenessRequest) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    selfie = body.selfie or body.image or "mocked-selfie-b64"
    if not selfie:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="selfie required")
    result = mock_liveness(selfie, sid)
    if result.get("status") == "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=result.get("error", "liveness failed"))
    return result

class BuyerVerifyRequest(BaseModel):
    email: str = Field(..., max_length=320)
    phone: str = Field(..., description="E164 international e.g. +14155551234 or +971501234567", max_length=20)
    country: str = Field(..., description="ISO2 e.g. US, AE, GB", min_length=2, max_length=2)
    address: str | None = Field(None, max_length=500)
    passport_mock: str | None = Field(None, description="base64 or file ref mocked", max_length=2000)
    user_id: str | None = None
    seller_id: str | None = None

class SahayakVerifyRequest(BaseModel):
    center_code: str = Field(..., description="DNK center allowlist code")
    employee_id: str = Field(..., pattern=r"^DNK-EMP-\d{4}$")
    email: str = Field(..., max_length=320)
    phone: str = Field(..., max_length=20)
    user_id: str | None = None
    seller_id: str | None = None

@router.post("/buyer")
async def verify_buyer(body: BuyerVerifyRequest) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    result = mock_buyer(body.phone, body.country, body.email, sid, body.address, body.passport_mock)
    if result.get("status") == "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=result.get("error", "buyer validation failed"))
    return result

@router.post("/sahayak")
async def verify_sahayak(body: SahayakVerifyRequest) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    result = mock_sahayak(body.center_code, body.employee_id, body.email, body.phone, sid)
    if result.get("status") == "failed":
        from fastapi import HTTPException
        err = result.get("error", "sahayak validation failed")
        code = 403 if "allowlist" in str(err) else 422
        raise HTTPException(status_code=code, detail=err)
    return result

@trust_router.get("/trust/{user_id}")
async def get_trust_level(user_id: str, role: str | None = None) -> dict[str, Any]:
    return get_trust(user_id, role)

class HumanGateRequest(BaseModel):
    seller_id: str | None = None
    user_id: str | None = None
    current_ad: str = Field(..., pattern=r"^\d{14}$")
    proposed_ad: str = Field(..., pattern=r"^\d{14}$")
    current_ifsc: str | None = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    proposed_ifsc: str | None = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    current_ad_code: str | None = None
    proposed_ad_code: str | None = None

@bindings_router.post("/confirm-human-gate")
async def confirm_gate(body: HumanGateRequest) -> dict[str, Any]:
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    cur = body.current_ad or body.current_ad_code or ""
    prop = body.proposed_ad or body.proposed_ad_code or ""
    return confirm_human_gate(sid, cur, prop, body.current_ifsc, body.proposed_ifsc)

class CashfreeRequest(BaseModel):
    pan: str | None = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    account_number: str | None = None
    bank_account: str | None = None
    ifsc: str | None = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    seller_id: str | None = None
    user_id: str | None = None

@router.post("/cashfree/bundle")
async def cashfree_bundle(body: CashfreeRequest) -> dict[str, Any]:
    pan = body.pan
    acct = body.bank_account or body.account_number
    ifsc = body.ifsc
    sid = _resolve_seller_id(body.seller_id, body.user_id)
    res = mock_cashfree_bundle(pan=pan, account_number=acct, ifsc=ifsc, seller_id=sid)
    _ = sid
    return res

@router.post("/cashfree/secure-id")
async def cashfree_secure_id(body: CashfreeRequest) -> dict[str, Any]:
    return await cashfree_bundle(body)

# ---------------------------------------------------------------------------
# Legacy generic endpoint kept for compat — MUST BE LAST
# ---------------------------------------------------------------------------

class VerifyRequest(BaseModel):
    seller_id: str | None = None
    pan: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    account_number: str | None = None
    ifsc: str | None = None

class VerifyResponse(BaseModel):
    level: str
    status: str
    mocked: bool = True
    verification_mode: str = "mock"
    provider: str = "mock"
    provider_request_id: str | None = None
    next_level: str | None = None
    trust_level: str | None = None
    trust_score: int | None = None
    is_verified: bool | None = None

_LEVEL_MAP: dict[str, VerificationLevel] = {
    "l0": VerificationLevel.L0,
    "l1": VerificationLevel.L1,
    "l2": VerificationLevel.L2,
    "liveness": VerificationLevel.LIVENESS,
    "l3": VerificationLevel.L3,
}

@router.post("/{level}")
async def verify_level(level: Literal["l0", "l1", "l2", "liveness", "l3"], body: VerifyRequest | None = None) -> VerifyResponse:
    _ = body
    key = level.lower()
    vl = _LEVEL_MAP[key]
    result = mock_verify(vl)
    return VerifyResponse(level=result.level.value, status=result.status.value, mocked=result.mocked, verification_mode="mock", provider="mock", provider_request_id=result.provider_request_id, next_level=result.next_level.value if result.next_level else None, trust_level=result.trust_level, trust_score=result.trust_score, is_verified=result.is_verified)
