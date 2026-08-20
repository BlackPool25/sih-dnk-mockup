"""Verification router — POST /verify/{level} mocked endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.state import VerificationLevel, mock_verify

router = APIRouter(prefix="/verify", tags=["verify"])


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
    next_level: str | None = None


_LEVEL_MAP: dict[str, VerificationLevel] = {
    "l0": VerificationLevel.L0,
    "l1": VerificationLevel.L1,
    "l2": VerificationLevel.L2,
    "liveness": VerificationLevel.LIVENESS,
}


@router.post("/{level}")
async def verify_level(
    level: Literal["l0", "l1", "l2", "liveness"],
    body: VerifyRequest | None = None,
) -> VerifyResponse:
    _ = body
    vl = _LEVEL_MAP[level]
    result = mock_verify(vl)
    return VerifyResponse(
        level=result.level.value,
        status=result.status.value,
        mocked=result.mocked,
        verification_mode="mock",
        provider="mock",
        next_level=result.next_level.value if result.next_level else None,
    )
