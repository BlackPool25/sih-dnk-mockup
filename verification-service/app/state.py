"""Verification state machine — mocked L0→L1→L2→L3 for demo."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum

class VerificationLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    LIVENESS = "liveness"

class VerificationStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass(frozen=True, slots=True)
class TransitionResult:
    level: VerificationLevel
    status: VerificationStatus
    mocked: bool = True
    next_level: VerificationLevel | None = None
    trust_level: str | None = None
    trust_score: int | None = None
    is_verified: bool = False
    verification_mode: str = "mock"
    provider_request_id: str = field(default_factory=lambda: f"mocked-{uuid.uuid4().hex[:12]}")

_LEVEL_ORDER: list[VerificationLevel] = [
    VerificationLevel.L0,
    VerificationLevel.L1,
    VerificationLevel.L2,
    VerificationLevel.L3,
]

_NEXT: dict[VerificationLevel, VerificationLevel | None] = {
    VerificationLevel.L0: VerificationLevel.L1,
    VerificationLevel.L1: VerificationLevel.L2,
    VerificationLevel.L2: VerificationLevel.L3,
    VerificationLevel.L3: None,
    VerificationLevel.LIVENESS: None,
}

_SCORE: dict[str, int] = {"L0": 25, "L1": 50, "L2": 85, "L3": 100, "liveness": 100}

_TRUST_STORE: dict[str, dict[str, object]] = {}
_HUMAN_GATE_STORE: dict[str, dict[str, object]] = {}

_PHONE_RE = re.compile(r"^[6-9]\d{9}$")
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_AADHAAR_RE = re.compile(r"^\d{12}$")
_IEC_RE = re.compile(r"^\d{10}$")
_AD_RE = re.compile(r"^\d{14}$")
_IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

_E164_RE = re.compile(r"^\+\d{7,15}$")
_ISO2_RE = re.compile(r"^[A-Z]{2}$")
_EMP_RE = re.compile(r"^DNK-EMP-\d{4}$")
SAHAYAK_CENTERS: list[str] = ["DNK-BLR-01", "DNK-DEL-01", "DNK-MUM-01", "DNK-DEL-02"]
_SAHAYAK_CENTER_SET: set[str] = set(SAHAYAK_CENTERS)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _valid_upto(minutes: int = 10) -> str:
    return (_now() + timedelta(minutes=minutes)).isoformat()

def _provider_id() -> str:
    return f"mocked-{uuid.uuid4().hex[:16]}"

def next_required_level(current: VerificationLevel | None) -> VerificationLevel | None:
    if current is None:
        return VerificationLevel.L0
    return _NEXT.get(current)

def mock_verify(level: VerificationLevel) -> TransitionResult:
    return TransitionResult(
        level=level,
        status=VerificationStatus.SUCCESS,
        mocked=True,
        next_level=_NEXT.get(level),
        trust_level=level.value,
        trust_score=_SCORE.get(level.value, 0),
        is_verified=level in (VerificationLevel.L2, VerificationLevel.L3),
        verification_mode="mock",
        provider_request_id=_provider_id(),
    )

def mock_l0(phone: str, seller_id: str) -> dict[str, object]:
    if not _PHONE_RE.match(phone):
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid phone format"}
    rec = {"level": "L0","status": "success","mocked": True,"verification_mode": "mock","provider": "mock_otp","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": _SCORE["L0"],"is_verified": False,"otp_mocked": True,"otp": "123456","validUpto": _valid_upto(10),"next_level": "L1"}
    _TRUST_STORE[seller_id] = {"level": "L0","score": _SCORE["L0"],"is_verified": False,"human_gate_confirmed": False,"updated_at": _now().isoformat()}
    return rec

def mock_l1(pan: str, aadhaar: str, seller_id: str) -> dict[str, object]:
    if not _PAN_RE.match(pan):
        return {"level": "L1","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_digilocker","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": _SCORE["L0"],"is_verified": False,"error": "invalid PAN"}
    if not _AADHAAR_RE.match(aadhaar):
        return {"level": "L1","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_digilocker","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": _SCORE["L0"],"is_verified": False,"error": "invalid Aadhaar"}
    rec = {"level": "L1","status": "success","mocked": True,"verification_mode": "mock","provider": "mock_digilocker","provider_request_id": _provider_id(),"trust_level": "L1","trust_score": _SCORE["L1"],"is_verified": False,"digilocker": {"pan_status": "valid","aadhaar_status": "valid","mode": "mock"},"next_level": "L2"}
    _TRUST_STORE[seller_id] = {"level": "L1","score": _SCORE["L1"],"is_verified": False,"human_gate_confirmed": False,"updated_at": _now().isoformat()}
    return rec

def mock_l2(iec: str, ad_code: str, bank_account: str, ifsc: str, seller_id: str) -> dict[str, object]:
    if not _IEC_RE.match(iec):
        return {"level": "L2","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_iec","provider_request_id": _provider_id(),"error": "invalid IEC"}
    if not _AD_RE.match(ad_code):
        return {"level": "L2","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_ad","provider_request_id": _provider_id(),"error": "invalid AD code — must be 14 digits"}
    if not _IFSC_RE.match(ifsc):
        return {"level": "L2","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_bank","provider_request_id": _provider_id(),"error": "invalid IFSC"}
    valid_upto = _valid_upto(10)
    result: dict[str, object] = {"level": "L2","status": "success","mocked": True,"verification_mode": "mock","provider": "mock_iec_bank_penny","provider_request_id": _provider_id(),"trust_level": "L2","trust_score": _SCORE["L2"],"is_verified": True,"iec_view_any": {"iec": iec,"status": "valid","mode": "mock"},"bank_penny": {"account": bank_account[-4:] if len(bank_account) >=4 else bank_account,"ifsc": ifsc,"penny_status": "credited","amount_minor": 100,"mode": "mock"},"reverse_penny": {"upi": f"mock-upi-{bank_account[-4:]}@mock","amount_minor": 100,"validUpto": valid_upto,"mode": "mock"},"reverse_upi": f"mock-upi-{bank_account[-4:]}@mock","validUpto": valid_upto,"ad_code": ad_code,"ad_code_valid": True,"human_gate_confirmed": False,"human_gate_required": True,"next_level": "L3"}
    _TRUST_STORE[seller_id] = {"level": "L2","score": _SCORE["L2"],"is_verified": True,"human_gate_confirmed": False,"iec": iec,"ad_code": ad_code,"ifsc": ifsc,"bank_account": bank_account,"validUpto": valid_upto,"updated_at": _now().isoformat()}
    _HUMAN_GATE_STORE[seller_id] = {"current_ad": ad_code,"current_ifsc": ifsc,"proposed_ad": ad_code,"proposed_ifsc": ifsc,"human_gate_confirmed": False}
    return result

def mock_liveness(selfie: str | None, seller_id: str) -> dict[str, object]:
    if not selfie:
        return {"level": "L3","status": "failed","mocked": True,"verification_mode": "mock","error": "selfie required"}
    result: dict[str, object] = {"level": "L3","status": "success","mocked": True,"verification_mode": "mock","provider": "mock_liveness","provider_request_id": _provider_id(),"trust_level": "L3","trust_score": _SCORE["L3"],"is_verified": True,"liveness_badge": True,"badge": "liveness_verified","next_level": None}
    existing = _TRUST_STORE.get(seller_id, {})
    existing.update({"level": "L3","score": _SCORE["L3"],"is_verified": True,"liveness": True,"updated_at": _now().isoformat()})
    _TRUST_STORE[seller_id] = existing
    return result

def mock_buyer(phone: str, country: str, email: str, seller_id: str, address: str | None = None, passport_mock: str | None = None) -> dict[str, object]:
    if not _E164_RE.match(phone):
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_cashfree","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid buyer phone — must be E164 e.g. +14155551234"}
    if not _ISO2_RE.match(country.upper()):
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_cashfree","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid country — must be ISO2 e.g. US, AE"}
    if "@" not in email:
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_cashfree","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid email"}
    _ = (address, passport_mock)
    rec: dict[str, object] = {"level": "L0","status": "success","role": "buyer","mocked": True,"verification_mode": "mock","provider": "mock_cashfree","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": _SCORE["L0"],"is_verified": True,"note": "foreign buyer — no PAN verification","country": country.upper(),"phone": phone,"email": email,"passport_mock": bool(passport_mock),"address": address}
    _TRUST_STORE[seller_id] = {"level": "L0","score": _SCORE["L0"],"is_verified": True,"role": "buyer","country": country.upper(),"phone": phone,"email": email,"human_gate_confirmed": False,"updated_at": _now().isoformat()}
    return rec

def mock_sahayak(center_code: str, employee_id: str, email: str, phone: str, seller_id: str) -> dict[str, object]:
    if center_code not in _SAHAYAK_CENTER_SET:
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_sahayak_allowlist","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": f"center_code not in allowlist {SAHAYAK_CENTERS}","allowlist": SAHAYAK_CENTERS}
    if not _EMP_RE.match(employee_id):
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_sahayak_allowlist","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid employee_id — must match ^DNK-EMP-\\d{4}$"}
    if "@" not in email:
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_sahayak_allowlist","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid email"}
    if not _E164_RE.match(phone) and not _PHONE_RE.match(phone):
        return {"level": "L0","status": "failed","mocked": True,"verification_mode": "mock","provider": "mock_sahayak_allowlist","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": 0,"is_verified": False,"error": "invalid phone — must be E164 (+...) or Indian 10-digit"}
    is_dnk_domain = email.lower().endswith("@dnk.gov.in")
    rec2: dict[str, object] = {"level": "L0","status": "success","role": "sahayak","mocked": True,"verification_mode": "mock","provider": "mock_sahayak_allowlist","provider_request_id": _provider_id(),"trust_level": "L0","trust_score": _SCORE["L0"],"is_verified": True,"center_code": center_code,"employee_id": employee_id,"email": email,"phone": phone,"email_domain_ok": is_dnk_domain,"note": "sahayak allowlist verified (mock)","allowlist": SAHAYAK_CENTERS}
    _TRUST_STORE[seller_id] = {"level": "L0","score": _SCORE["L0"],"is_verified": True,"role": "sahayak","center_code": center_code,"employee_id": employee_id,"email": email,"phone": phone,"human_gate_confirmed": False,"updated_at": _now().isoformat()}
    return rec2

def get_trust(seller_id: str, role: str | None = None) -> dict[str, object]:
    rec = _TRUST_STORE.get(seller_id)
    if rec is None:
        return {"seller_id": seller_id,"level": "L0","trust_level": "L0","trust_score": 0,"score": 0,"is_verified": False,"mocked": True,"verification_mode": "mock","role": role}
    base: dict[str, object] = {"seller_id": seller_id,"level": rec.get("level","L0"),"trust_level": rec.get("level","L0"),"trust_score": rec.get("score",0),"score": rec.get("score",0),"is_verified": rec.get("is_verified",False),"human_gate_confirmed": rec.get("human_gate_confirmed",False),"mocked": True,"verification_mode": "mock","role": rec.get("role", role),"updated_at": rec.get("updated_at"),"validUpto": rec.get("validUpto")}
    if rec.get("role") == "buyer":
        base.update({"country": rec.get("country"),"phone": rec.get("phone")})
    if rec.get("role") == "sahayak":
        base.update({"center_code": rec.get("center_code"),"employee_id": rec.get("employee_id")})
    return base

def confirm_human_gate(seller_id: str, current_ad: str, proposed_ad: str, current_ifsc: str | None = None, proposed_ifsc: str | None = None) -> dict[str, object]:
    side_by_side = {"current_ad": current_ad,"proposed_ad": proposed_ad,"current_ifsc": current_ifsc,"proposed_ifsc": proposed_ifsc,"current_bank": (current_ifsc[:4] if current_ifsc else None),"proposed_bank": (proposed_ifsc[:4] if proposed_ifsc else None)}
    mismatch = current_ad != proposed_ad or (current_ifsc is not None and proposed_ifsc is not None and current_ifsc[:4] != proposed_ifsc[:4])
    if seller_id in _TRUST_STORE:
        _TRUST_STORE[seller_id]["human_gate_confirmed"] = True
        _TRUST_STORE[seller_id]["updated_at"] = _now().isoformat()
    if seller_id in _HUMAN_GATE_STORE:
        _HUMAN_GATE_STORE[seller_id].update({"current_ad": current_ad,"proposed_ad": proposed_ad,"human_gate_confirmed": True,"side_by_side": side_by_side})
    else:
        _HUMAN_GATE_STORE[seller_id] = {"current_ad": current_ad,"proposed_ad": proposed_ad,"human_gate_confirmed": True,"side_by_side": side_by_side}
    return {"seller_id": seller_id,"human_gate_confirmed": True,"mismatch_detected": mismatch,"side_by_side": side_by_side,"mocked": True,"verification_mode": "mock","provider": "mock_human_gate","provider_request_id": _provider_id(),"message": "Human gate confirmed (mocked)" if not mismatch else "Mismatch noted — hard block applies"}

def reset_stores() -> None:
    _TRUST_STORE.clear()
    _HUMAN_GATE_STORE.clear()
