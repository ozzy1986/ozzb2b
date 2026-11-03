"""Client leads → outreach drafts → admin-reviewed e-mails.

Flow:
1. The public form fetches a signed form token, the client submits a lead.
   Spam is filtered in-house: honeypot field, minimum fill time measured
   from the token, per-IP rate limit (route layer) and content heuristics.
2. We draft one e-mail per matching provider (category + e-mail present,
   not unsubscribed, same city first) and notify the admin by e-mail with
   a link to the review page.
3. The admin edits each draft and sends it by hand. Nothing is sent to
   providers automatically.
"""

from __future__ import annotations

import hashlib
import hmac
import html
import re
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.db.models import (
    Category,
    City,
    EmailSuppression,
    Lead,
    LeadStatus,
    OutreachMessage,
    OutreachStatus,
    Provider,
    ProviderCategory,
    ProviderStatus,
)
from ozzb2b_api.errors import ConflictError, NotFoundError, ValidationError
from ozzb2b_api.services import mailer
from ozzb2b_api.services.mailer import MailDeliveryError, OutgoingMail

log = structlog.get_logger("ozzb2b_api.services.leads")

_URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
_CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)
MAX_LINKS_IN_DESCRIPTION = 2

CATEGORY_PHRASE_RU: dict[str, str] = {
    "marketplace-accounting": "бухгалтерское сопровождение продаж на маркетплейсах",
    "accounting": "бухгалтерское обслуживание",
    "bookkeeping": "ведение бухгалтерского учёта",
    "tax-advisory": "налоговая консультация",
    "payroll": "расчёт зарплаты и кадровый учёт",
    "audit-assurance": "аудит",
    "legal": "юридические услуги",
    "it": "IT-подрядчик",
    "software-development": "разработка ПО",
}
CITY_RU: dict[str, str] = {
    "Moscow": "Москва",
    "Saint Petersburg": "Санкт-Петербург",
    "Novosibirsk": "Новосибирск",
    "Yekaterinburg": "Екатеринбург",
    "Kazan": "Казань",
    "Nizhny Novgorod": "Нижний Новгород",
    "Samara": "Самара",
    "Rostov-on-Don": "Ростов-на-Дону",
    "Krasnodar": "Краснодар",
    "Perm": "Пермь",
    "Voronezh": "Воронеж",
    "Ufa": "Уфа",
    "Chelyabinsk": "Челябинск",
    "Tyumen": "Тюмень",
    "Omsk": "Омск",
}


class LeadRejectedError(ValidationError):
    """The submission looks like spam or the form token is invalid."""


class OutreachNotEditableError(ConflictError):
    """Only drafts (or failed sends) can be edited or sent."""


class RecipientSuppressedError(ConflictError):
    """The recipient asked not to be contacted."""


# --- anti-spam -------------------------------------------------------------


def _sign(cfg: Settings, purpose: str, payload: str) -> str:
    key = cfg.jwt_secret.encode()
    return hmac.new(key, f"{purpose}:{payload}".encode(), hashlib.sha256).hexdigest()[:32]


def issue_form_token(cfg: Settings | None = None, *, now: float | None = None) -> str:
    cfg = cfg or get_settings()
    payload = f"{int(now if now is not None else time.time())}.{secrets.token_hex(8)}"
    return f"{payload}.{_sign(cfg, 'lead-form', payload)}"


def check_form_token(token: str, cfg: Settings | None = None, *, now: float | None = None) -> None:
    """Reject forged, expired or suspiciously fast submissions."""
    cfg = cfg or get_settings()
    issued_raw, _, rest = token.partition(".")
    nonce, _, sig = rest.partition(".")
    if not (issued_raw.isdigit() and nonce and sig):
        raise LeadRejectedError("invalid form token")
    if not hmac.compare_digest(sig, _sign(cfg, "lead-form", f"{issued_raw}.{nonce}")):
        raise LeadRejectedError("invalid form token")
    age = (now if now is not None else time.time()) - int(issued_raw)
    if age > cfg.lead_form_token_ttl_seconds:
        raise LeadRejectedError("form token expired")
    if age < cfg.lead_min_fill_seconds:
        raise LeadRejectedError("form submitted too fast")


def check_content(description: str) -> None:
    if len(_URL_RE.findall(description)) > MAX_LINKS_IN_DESCRIPTION:
        raise LeadRejectedError("too many links")
    if not _CYRILLIC_RE.search(description):
        raise LeadRejectedError("description must be in Russian")


def unsubscribe_token(email: str, cfg: Settings | None = None) -> str:
    return _sign(cfg or get_settings(), "unsubscribe", email.strip().lower())


def unsubscribe_url(email: str, cfg: Settings | None = None) -> str:
    cfg = cfg or get_settings()
    query = urlencode({"email": email, "token": unsubscribe_token(email, cfg)})
    return f"{cfg.public_site_url.rstrip('/')}/unsubscribe?{query}"


# --- drafting --------------------------------------------------------------


@dataclass(frozen=True)
class LeadInput:
    category_slug: str
    city_id: int | None
    description: str
    budget: str | None
    contact_name: str
    contact_email: str
    contact_phone: str | None
    company_name: str | None
    source_ip: str | None
    user_agent: str | None


def category_phrase(category: Category | None) -> str:
    if category is None:
        return "подрядчик"
    return CATEGORY_PHRASE_RU.get(category.slug, category.name)


def city_phrase(city: City | None) -> str:
    if city is None:
        return "город не важен, можно удалённо"
    return CITY_RU.get(city.name, city.name)


def render_draft(lead: Lead, provider: Provider, cfg: Settings) -> tuple[str, str]:
    """Subject and plain-text body of the first e-mail to a provider."""
    need = category_phrase(lead.category)
    subject = f"Заявка от клиента: {need}"
    found_on = provider.website or "открытых источниках"
    lines = [
        "Здравствуйте!",
        "",
        "Пишу из ozzb2b.com — это каталог подрядчиков для бизнеса. "
        f"К нам обратился клиент, которому нужна услуга: {need}. "
        f"Ваша компания подходит под запрос — мы нашли её на сайте {found_on}.",
        "",
        "Суть запроса:",
        lead.description.strip(),
        "",
        f"Город: {city_phrase(lead.city)}",
    ]
    if lead.budget:
        lines.append(f"Бюджет: {lead.budget}")
    lines += [
        "",
        "Если вам интересно, просто ответьте на это письмо — передадим контакты клиента. "
        "Если запрос не ваш профиль, тоже напишите: больше не побеспокоим.",
        "Регистрироваться и платить ничего не нужно.",
        "",
        "--",
        "ozzb2b.com",
        f"Не хотите получать такие письма: {unsubscribe_url(provider.email or '', cfg)}",
    ]
    return subject, "\n".join(lines)


async def _suppressed(session: AsyncSession, email: str) -> bool:
    row = await session.execute(
        select(EmailSuppression.id).where(EmailSuppression.email == email.strip().lower())
    )
    return row.first() is not None


async def match_providers(session: AsyncSession, lead: Lead, limit: int) -> list[Provider]:
    """Providers in the lead's category (or its subcategories) we can e-mail."""
    if lead.category_id is None:
        return []
    child_ids = select(Category.id).where(Category.parent_id == lead.category_id)
    in_category = select(ProviderCategory.provider_id).where(
        (ProviderCategory.category_id == lead.category_id)
        | ProviderCategory.category_id.in_(child_ids)
    )
    suppressed = select(EmailSuppression.email)
    same_city = case((Provider.city_id == lead.city_id, 0), else_=1)
    # Membership via IN (not JOIN + DISTINCT): Postgres rejects DISTINCT with an
    # ORDER BY expression that isn't selected, and a provider may sit in
    # several matching categories.
    stmt = (
        select(Provider)
        .where(
            Provider.id.in_(in_category),
            Provider.status == ProviderStatus.PUBLISHED,
            Provider.email.is_not(None),
            Provider.email != "",
            func.lower(Provider.email).not_in(suppressed),
        )
        .order_by(same_city, Provider.is_claimed.desc(), Provider.display_name)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars())


async def create_lead(
    session: AsyncSession, data: LeadInput, cfg: Settings | None = None
) -> tuple[Lead, int]:
    """Persist the lead and its outreach drafts; returns (lead, drafts created)."""
    cfg = cfg or get_settings()
    category = (
        await session.execute(select(Category).where(Category.slug == data.category_slug))
    ).scalar_one_or_none()
    if category is None:
        raise NotFoundError("category not found")
    city = await session.get(City, data.city_id) if data.city_id is not None else None
    lead = Lead(
        id=uuid.uuid4(),
        category_id=category.id,
        city_id=city.id if city else None,
        description=data.description.strip(),
        budget=(data.budget or "").strip() or None,
        contact_name=data.contact_name.strip(),
        contact_email=data.contact_email.strip().lower(),
        contact_phone=(data.contact_phone or "").strip() or None,
        company_name=(data.company_name or "").strip() or None,
        consent_at=datetime.now(tz=UTC),
        status=LeadStatus.NEW,
        source_ip=data.source_ip,
        user_agent=(data.user_agent or "")[:255] or None,
    )
    lead.category = category
    lead.city = city
    session.add(lead)
    await session.flush()

    providers = await match_providers(session, lead, cfg.lead_max_drafts)
    for provider in providers:
        subject, body = render_draft(lead, provider, cfg)
        session.add(
            OutreachMessage(
                lead_id=lead.id,
                provider_id=provider.id,
                to_email=(provider.email or "").strip().lower(),
                subject=subject,
                body=body,
                status=OutreachStatus.DRAFT,
            )
        )
    await session.flush()
    log.info("lead.created", lead_id=str(lead.id), category=category.slug, drafts=len(providers))
    return lead, len(providers)


def admin_notification(lead: Lead, drafts: int, cfg: Settings) -> OutgoingMail | None:
    if not cfg.admin_notify_email:
        return None
    url = f"{cfg.public_site_url.rstrip('/')}/admin/leads/{lead.id}"
    need = category_phrase(lead.category)
    summary = [
        f"Услуга: {need}",
        f"Город: {city_phrase(lead.city)}",
        f"Бюджет: {lead.budget or 'не указан'}",
        f"Клиент: {lead.contact_name}" + (f", {lead.company_name}" if lead.company_name else ""),
        f"Черновиков писем подрядчикам: {drafts}",
    ]
    text = "\n".join(
        ["Новая заявка на ozzb2b.com", "", *summary, "", lead.description, "", f"Открыть: {url}"]
    )
    esc = html.escape
    items = "".join(f"<li>{esc(line)}</li>" for line in summary)
    page = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;color:#0f172a">'
        '<h2 style="margin:0 0 12px">Новая заявка на ozzb2b.com</h2>'
        f'<ul style="padding-left:18px">{items}</ul>'
        f'<p style="white-space:pre-wrap">{esc(lead.description)}</p>'
        f'<p><a href="{esc(url)}" style="display:inline-block;padding:12px 20px;'
        "background:#2563eb;color:#fff;border-radius:8px;text-decoration:none;"
        'font-weight:bold">Проверить и отправить письма</a></p>'
        "</div>"
    )
    return OutgoingMail(
        to=cfg.admin_notify_email,
        subject=f"Новая заявка: {need} ({city_phrase(lead.city)})",
        body=text,
        html=page,
    )


def client_confirmation(lead: Lead, cfg: Settings) -> OutgoingMail:
    """Receipt for the client. Echoes none of the free text: the address is
    unverified, so the form must not become a relay for arbitrary content."""
    need = category_phrase(lead.category)
    text = "\n".join(
        [
            f"Здравствуйте, {lead.contact_name}!",
            "",
            f"Мы получили вашу заявку на ozzb2b.com: {need}, {city_phrase(lead.city)}.",
            "",
            "Сейчас подбираем подрядчиков под ваш запрос и отправляем им его описание. "
            "Ваши контакты получат только те, кто откликнется, — они напишут вам сами.",
            "",
            "Подходящих подрядчиков может и не найтись. В этом случае мы тоже напишем, "
            "чтобы вы не ждали зря.",
            "",
            "Если заявку отправляли не вы, просто проигнорируйте это письмо.",
            "",
            "--",
            "ozzb2b.com",
        ]
    )
    return OutgoingMail(
        to=lead.contact_email,
        subject="Заявка принята — подбираем подрядчиков",
        body=text,
        reply_to=cfg.admin_notify_email or None,
    )


async def send_quietly(mail: OutgoingMail, cfg: Settings | None = None) -> None:
    """Best effort: a failed notification must not lose the lead."""
    try:
        await mailer.send_mail(mail, cfg)
    except MailDeliveryError:
        log.warning("lead.mail_failed", to=mail.to)


# --- admin -----------------------------------------------------------------


async def list_leads(session: AsyncSession, *, limit: int = 100) -> list[Lead]:
    stmt = (
        select(Lead)
        .options(
            selectinload(Lead.category),
            selectinload(Lead.city),
            selectinload(Lead.outreach),
        )
        .order_by(Lead.created_at.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars())


async def get_lead(session: AsyncSession, lead_id: uuid.UUID) -> Lead:
    stmt = (
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.category),
            selectinload(Lead.city),
            selectinload(Lead.outreach).selectinload(OutreachMessage.provider),
        )
    )
    lead = (await session.execute(stmt)).scalar_one_or_none()
    if lead is None:
        raise NotFoundError("lead not found")
    return lead


async def update_lead(
    session: AsyncSession, lead_id: uuid.UUID, *, status: LeadStatus | None, note: str | None
) -> Lead:
    lead = await get_lead(session, lead_id)
    if status is not None:
        lead.status = status
    if note is not None:
        lead.admin_note = note.strip() or None
    await session.flush()
    return lead


async def _get_outreach(session: AsyncSession, outreach_id: uuid.UUID) -> OutreachMessage:
    stmt = (
        select(OutreachMessage)
        .where(OutreachMessage.id == outreach_id)
        .options(selectinload(OutreachMessage.provider))
    )
    msg = (await session.execute(stmt)).scalar_one_or_none()
    if msg is None:
        raise NotFoundError("outreach message not found")
    return msg


async def _flush_outreach(session: AsyncSession, msg: OutreachMessage) -> OutreachMessage:
    """Flush and reload DB-maintained timestamps.

    ``updated_at`` is expired by the flush (``onupdate=now()``); reading it later
    from sync code (Pydantic serialisation) would trigger a lazy load outside the
    async greenlet and crash with MissingGreenlet.
    """
    await session.flush()
    await session.refresh(msg, ["created_at", "updated_at"])
    return msg


def _ensure_editable(msg: OutreachMessage) -> None:
    if msg.status not in (OutreachStatus.DRAFT, OutreachStatus.FAILED):
        raise OutreachNotEditableError("outreach message already processed")


async def add_draft(
    session: AsyncSession, lead_id: uuid.UUID, provider_slug: str, cfg: Settings | None = None
) -> OutreachMessage:
    cfg = cfg or get_settings()
    lead = await get_lead(session, lead_id)
    provider = (
        await session.execute(select(Provider).where(Provider.slug == provider_slug))
    ).scalar_one_or_none()
    if provider is None:
        raise NotFoundError("provider not found")
    if any(m.provider_id == provider.id for m in lead.outreach):
        raise ConflictError("draft for this provider already exists")
    subject, body = render_draft(lead, provider, cfg)
    msg = OutreachMessage(
        lead_id=lead.id,
        provider_id=provider.id,
        to_email=(provider.email or "").strip().lower(),
        subject=subject,
        body=body,
        status=OutreachStatus.DRAFT,
    )
    msg.provider = provider
    session.add(msg)
    return await _flush_outreach(session, msg)


async def update_outreach(
    session: AsyncSession,
    outreach_id: uuid.UUID,
    *,
    to_email: str | None,
    subject: str | None,
    body: str | None,
) -> OutreachMessage:
    msg = await _get_outreach(session, outreach_id)
    _ensure_editable(msg)
    if to_email is not None:
        msg.to_email = to_email.strip().lower()
    if subject is not None:
        msg.subject = subject.strip()
    if body is not None:
        msg.body = body
    return await _flush_outreach(session, msg)


async def skip_outreach(session: AsyncSession, outreach_id: uuid.UUID) -> OutreachMessage:
    msg = await _get_outreach(session, outreach_id)
    _ensure_editable(msg)
    msg.status = OutreachStatus.SKIPPED
    return await _flush_outreach(session, msg)


async def send_outreach(
    session: AsyncSession, outreach_id: uuid.UUID, cfg: Settings | None = None
) -> OutreachMessage:
    cfg = cfg or get_settings()
    msg = await _get_outreach(session, outreach_id)
    _ensure_editable(msg)
    if not msg.to_email:
        raise ValidationError("recipient e-mail is empty")
    if await _suppressed(session, msg.to_email):
        raise RecipientSuppressedError("recipient unsubscribed")
    try:
        await mailer.send_mail(
            OutgoingMail(
                to=msg.to_email,
                subject=msg.subject,
                body=msg.body,
                list_unsubscribe=unsubscribe_url(msg.to_email, cfg),
            ),
            cfg,
        )
    except MailDeliveryError as exc:
        msg.status = OutreachStatus.FAILED
        msg.error = str(exc)[:2000]
        return await _flush_outreach(session, msg)
    msg.status = OutreachStatus.SENT
    msg.sent_at = datetime.now(tz=UTC)
    msg.error = None
    return await _flush_outreach(session, msg)


async def delete_outreach(session: AsyncSession, outreach_id: uuid.UUID) -> None:
    """Drop a message that never went out; sent ones stay as a record."""
    msg = await _get_outreach(session, outreach_id)
    if msg.status == OutreachStatus.SENT:
        raise OutreachNotEditableError("outreach message already sent")
    await session.delete(msg)
    await session.flush()


async def lead_outreach_ids(session: AsyncSession, lead_id: uuid.UUID) -> set[uuid.UUID]:
    rows = await session.execute(
        select(OutreachMessage.id).where(OutreachMessage.lead_id == lead_id)
    )
    return set(rows.scalars())


async def unsubscribe(
    session: AsyncSession, email: str, token: str, cfg: Settings | None = None
) -> None:
    normalized = email.strip().lower()
    if not hmac.compare_digest(token, unsubscribe_token(normalized, cfg)):
        raise ValidationError("invalid unsubscribe link")
    if await _suppressed(session, normalized):
        return
    session.add(EmailSuppression(email=normalized, reason="unsubscribe_link"))
    await session.flush()
