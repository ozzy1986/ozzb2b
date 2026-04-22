"""Claim-flow request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClaimInitiateResponse(BaseModel):
    claim_id: uuid.UUID
    status: str
    token: str
    meta_tag: str
    instructions: str


class ClaimPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    method: str
    verified_at: datetime | None
    rejected_at: datetime | None
    rejected_reason: str | None
    created_at: datetime
    updated_at: datetime


class ClaimRejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class ProviderUpdateRequest(BaseModel):
    """Subset of provider fields the owner is allowed to update."""

    display_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
