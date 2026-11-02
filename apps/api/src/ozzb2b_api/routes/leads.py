"""Client leads (public form) and the admin outreach review endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response, status

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import Lead, OutreachStatus, User, UserRole
from ozzb2b_api.errors import ForbiddenError, ValidationError
from ozzb2b_api.routes.deps import DbSession, get_current_user
from ozzb2b_api.schemas.leads import (
    LeadCreateRequest,
    LeadCreateResponse,
    LeadDetail,
    LeadFormToken,
    LeadSummary,
    LeadUpdateRequest,
    OutreachAddRequest,
    OutreachPublic,
    OutreachUpdateRequest,
    UnsubscribeRequest,
)
from ozzb2b_api.security.rate_limit import client_ip, enforce_rate_limit
from ozzb2b_api.services import leads as leads_service

router = APIRouter(tags=["leads"])
admin_router = APIRouter(prefix="/admin/leads", tags=["admin"])


def _require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("admin only")
    return user


AdminUser = Annotated[User, Depends(_require_admin)]


@router.get("/leads/form-token", response_model=LeadFormToken)
async def lead_form_token(response: Response) -> LeadFormToken:
    response.headers["Cache-Control"] = "no-store"
    return LeadFormToken(token=leads_service.issue_form_token())


@router.post(
    "/leads",
    response_model=LeadCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lead(
    payload: LeadCreateRequest,
    request: Request,
    response: Response,
    background: BackgroundTasks,
    db: DbSession,
) -> LeadCreateResponse:
    cfg = get_settings()
    await enforce_rate_limit(
        request=request,
        response=response,
        endpoint="lead_create",
        limit=cfg.rate_limit_lead_max,
        user_scope=str(payload.contact_email).lower(),
    )
    # Honeypot hit: answer like a success so the bot learns nothing.
    if payload.website:
        return LeadCreateResponse()
    if not payload.consent:
        raise ValidationError("consent required")
    leads_service.check_form_token(payload.form_token, cfg)
    leads_service.check_content(payload.description)

    headers = {k.lower(): v for k, v in request.headers.items()}
    lead, drafts = await leads_service.create_lead(
        db,
        leads_service.LeadInput(
            category_slug=payload.category_slug,
            city_id=payload.city_id,
            description=payload.description,
            budget=payload.budget,
            contact_name=payload.contact_name,
            contact_email=str(payload.contact_email),
            contact_phone=payload.contact_phone,
            company_name=payload.company_name,
            source_ip=client_ip(
                headers,
                request.client.host if request.client else None,
                trusted_proxy_count=cfg.trusted_proxy_count,
            ),
            user_agent=headers.get("user-agent"),
        ),
        cfg,
    )
    mail = leads_service.admin_notification(lead, drafts, cfg)
    if mail is not None:
        background.add_task(leads_service.send_quietly, mail)
    return LeadCreateResponse()


@router.post("/email/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(payload: UnsubscribeRequest, db: DbSession) -> Response:
    await leads_service.unsubscribe(db, str(payload.email), payload.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- admin -----------------------------------------------------------------


def _summary(lead: Lead) -> dict[str, object]:
    return {
        "id": lead.id,
        "status": lead.status.value,
        "category_slug": lead.category.slug if lead.category else None,
        "category_name": lead.category.name if lead.category else None,
        "city_name": lead.city.name if lead.city else None,
        "contact_name": lead.contact_name,
        "company_name": lead.company_name,
        "description": lead.description,
        "drafts": sum(1 for m in lead.outreach if m.status == OutreachStatus.DRAFT),
        "sent": sum(1 for m in lead.outreach if m.status == OutreachStatus.SENT),
        "created_at": lead.created_at,
    }


def _detail(lead: Lead) -> LeadDetail:
    return LeadDetail(
        **_summary(lead),
        budget=lead.budget,
        contact_email=lead.contact_email,
        contact_phone=lead.contact_phone,
        admin_note=lead.admin_note,
        outreach=[OutreachPublic.model_validate(m) for m in lead.outreach],
    )


@admin_router.get("", response_model=list[LeadSummary])
async def list_leads(
    db: DbSession,
    _admin: AdminUser,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[LeadSummary]:
    rows = await leads_service.list_leads(db, limit=limit)
    return [LeadSummary(**_summary(r)) for r in rows]


@admin_router.get("/{lead_id}", response_model=LeadDetail)
async def get_lead(lead_id: uuid.UUID, db: DbSession, _admin: AdminUser) -> LeadDetail:
    return _detail(await leads_service.get_lead(db, lead_id))


@admin_router.patch("/{lead_id}", response_model=LeadDetail)
async def update_lead(
    lead_id: uuid.UUID, payload: LeadUpdateRequest, db: DbSession, _admin: AdminUser
) -> LeadDetail:
    await leads_service.update_lead(
        db, lead_id, status=payload.status, note=payload.admin_note
    )
    return _detail(await leads_service.get_lead(db, lead_id))


@admin_router.post(
    "/{lead_id}/outreach", response_model=OutreachPublic, status_code=status.HTTP_201_CREATED
)
async def add_outreach(
    lead_id: uuid.UUID, payload: OutreachAddRequest, db: DbSession, _admin: AdminUser
) -> OutreachPublic:
    msg = await leads_service.add_draft(db, lead_id, payload.provider_slug)
    return OutreachPublic.model_validate(msg)


@admin_router.patch("/outreach/{outreach_id}", response_model=OutreachPublic)
async def update_outreach(
    outreach_id: uuid.UUID, payload: OutreachUpdateRequest, db: DbSession, _admin: AdminUser
) -> OutreachPublic:
    msg = await leads_service.update_outreach(
        db,
        outreach_id,
        to_email=str(payload.to_email) if payload.to_email else None,
        subject=payload.subject,
        body=payload.body,
    )
    return OutreachPublic.model_validate(msg)


@admin_router.post("/outreach/{outreach_id}/send", response_model=OutreachPublic)
async def send_outreach(
    outreach_id: uuid.UUID, db: DbSession, _admin: AdminUser
) -> OutreachPublic:
    msg = await leads_service.send_outreach(db, outreach_id)
    return OutreachPublic.model_validate(msg)


@admin_router.post("/outreach/{outreach_id}/skip", response_model=OutreachPublic)
async def skip_outreach(
    outreach_id: uuid.UUID, db: DbSession, _admin: AdminUser
) -> OutreachPublic:
    msg = await leads_service.skip_outreach(db, outreach_id)
    return OutreachPublic.model_validate(msg)
