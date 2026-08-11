"""Pydantic schemas for seller profile CRUD — request/response validation.

All encrypted fields use plaintext names (``pan``, ``bank_account``,
``ad_code``, ``gstin``) — the router is responsible for mapping to/from
the ``_encrypted`` PostgreSQL columns and calling the crypto service.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProfileCreateRequest(BaseModel):
    """Schema for POST /profile — all fields except firm_name are optional."""

    model_config = ConfigDict(extra="forbid")

    firm_name: str = Field(..., min_length=1, max_length=255)
    owner_name: str | None = Field(None, max_length=255)
    pan: str | None = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    bank_name: str | None = Field(None, max_length=255)
    bank_account: str | None = None
    ifsc: str | None = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    bank_branch: str | None = Field(None, max_length=255)
    iec: str | None = Field(None, pattern=r"^\d{10}$")
    ad_code: str | None = None
    gstin: str | None = None
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    phone: str | None = Field(None, max_length=20)


class ProfileUpdateRequest(BaseModel):
    """Schema for PUT /profile — all fields optional for partial update."""

    model_config = ConfigDict(extra="forbid")

    firm_name: str | None = Field(None, min_length=1, max_length=255)
    owner_name: str | None = Field(None, max_length=255)
    pan: str | None = None
    bank_name: str | None = Field(None, max_length=255)
    bank_account: str | None = None
    ifsc: str | None = None
    bank_branch: str | None = Field(None, max_length=255)
    iec: str | None = None
    ad_code: str | None = None
    gstin: str | None = None
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    phone: str | None = Field(None, max_length=20)


class ProfileResponse(BaseModel):
    """Schema for profile responses — all encrypted fields are decrypted."""

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
    profile_version: int = 1
    created_at: str
    updated_at: str
