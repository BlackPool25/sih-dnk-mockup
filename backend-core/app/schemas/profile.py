"""Pydantic schemas for seller profile CRUD — request/response validation.

All encrypted fields use plaintext names (``pan``, ``bank_account``,
``ad_code``, ``gstin``) — the router is responsible for mapping to/from
the ``_encrypted`` PostgreSQL columns and calling the crypto service.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProfileCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    firm_name: str = Field(..., min_length=1, max_length=255)
    owner_name: str | None = Field(None, max_length=255)
    pan: str | None = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    bank_name: str | None = Field(None, max_length=255)
    bank_account: str | None = None
    ifsc: str | None = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    bank_branch: str | None = Field(None, max_length=255)
    iec: str | None = Field(None, pattern=r"^\d{10}$")
    ad_code: str | None = Field(None, pattern=r"^\d{14}$")
    gstin: str | None = Field(None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, pattern=r"^[1-9][0-9]{5}$")
    phone: str | None = Field(None, pattern=r"^[6-9]\d{9}$")


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    firm_name: str | None = Field(None, min_length=1, max_length=255)
    owner_name: str | None = Field(None, max_length=255)
    pan: str | None = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    bank_name: str | None = Field(None, max_length=255)
    bank_account: str | None = None
    ifsc: str | None = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    bank_branch: str | None = Field(None, max_length=255)
    iec: str | None = Field(None, pattern=r"^\d{10}$")
    ad_code: str | None = Field(None, pattern=r"^\d{14}$")
    gstin: str | None = Field(None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, pattern=r"^[1-9][0-9]{5}$")
    phone: str | None = Field(None, pattern=r"^[6-9]\d{9}$")


class BuyerProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    email: str | None = Field(None, max_length=320)
    country: str | None = Field(None, max_length=64)
    phone: str | None = Field(None, max_length=20)


class BuyerProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    buyer_id: str
    name: str
    email: str | None = None
    country: str | None = None
    phone: str | None = None
    mocked: bool = True
    verification_mode: str = "mock"
    pan_required: bool = False
    note: str = "buyer foreign minimal mock — no PAN"


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    firm_name: str
    owner_name: str | None = None
    pan: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    ifsc: str | None = None
    bank_branch: str | None = None
    iec: str | None = None
    ad_code: str | None = None
    gstin: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
    is_verified: bool = False
    trust_level: str | None = None
    trust_score: int | None = None
    payouts_frozen: bool = False
    profile_version: int = 1
    created_at: str
    updated_at: str
    verification_mode: str = "mock"
    mocked: bool = True
