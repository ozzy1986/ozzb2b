"""Lead / outreach request and response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ozzb2b_api.db.models import LeadStatus


class LeadFormToken(BaseModel):
    token: str


class LeadCreateRequest(BaseModel):
    category_slug: str = Field(min_length=1, max_length=128)
    city_id: int | None = Field(default=None, ge=1)
    description: str = Field(min_length=20, max_length=4000)
    budget: str | None = Field(default=None, max_length=120)
    contact_name: str = Field(min_length=2, max_length=120)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=64)
    company_name: str | None = Field(default=None, max_length=255)
    consent: bool
    form_token: str = Field(min_length=10, max_length=200)
    # Honeypot: hidden from people, bots fill every field they see.
    website: str | None = Field(default=None, max_length=500)


class LeadCreateResponse(BaseModel):
    ok: bool = True


class UnsubscribeRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=8, max_length=128)


class OutreachProvider(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    display_name: str
    website: str | None
    is_claimed: bool


class OutreachPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: OutreachProvider
    to_email: str
    subject: str
    body: str
    status: str
    sent_at: datetime | None
    error: str | None
    updated_at: datetime


class LeadSummary(BaseModel):
    id: uuid.UUID
    status: str
    category_slug: str | None
    category_name: str | None
    city_name: str | None
    contact_name: str
    company_name: str | None
    description: str
    drafts: int
    sent: int
    created_at: datetime


class LeadDetail(LeadSummary):
    budget: str | None
    contact_email: str
    contact_phone: str | None
    admin_note: str | None
    outreach: list[OutreachPublic]


class LeadUpdateRequest(BaseModel):
    status: LeadStatus | None = None
    admin_note: str | None = Field(default=None, max_length=4000)


class OutreachUpdateRequest(BaseModel):
    to_email: EmailStr | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, min_length=1, max_length=20000)


class OutreachAddRequest(BaseModel):
    provider_slug: str = Field(min_length=1, max_length=160)
