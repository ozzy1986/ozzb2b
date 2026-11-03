"""Leads: anti-spam guards, outreach drafts, admin notification, mailer."""

from __future__ import annotations

import smtplib
import uuid
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from ozzb2b_api.config import Settings
from ozzb2b_api.db.models import Lead, Provider
from ozzb2b_api.services import leads as leads_service
from ozzb2b_api.services import mailer
from ozzb2b_api.services.leads import LeadRejectedError
from ozzb2b_api.services.mailer import MailDeliveryError, OutgoingMail


@pytest.fixture()
def cfg() -> Settings:
    return Settings(
        env="test",
        jwt_secret="unit-tests-secret-long-enough-for-hmac-sha256",
        public_site_url="https://ozzb2b.com",
        admin_notify_email="owner@example.com",
        mail_from="ozzb2b <noreply@ozzb2b.com>",
        lead_min_fill_seconds=4,
        lead_form_token_ttl_seconds=3600,
    )


def _lead(**overrides: Any) -> Lead:
    data: dict[str, Any] = {
        "id": uuid.uuid4(),
        "category": SimpleNamespace(slug="marketplace-accounting", name="x"),
        "city": SimpleNamespace(name="Kazan"),
        "description": "Нужен бухгалтер для ИП на Wildberries, УСН 6%, оборот 2 млн в месяц.",
        "budget": "до 15 000 ₽/мес",
        "contact_name": "Анна",
        "company_name": "ИП Петрова",
        "contact_email": "anna@client.ru",
    }
    data.update(overrides)
    return cast(Lead, SimpleNamespace(**data))


def _provider(email: str = "info@buh.ru") -> Provider:
    return cast(Provider, SimpleNamespace(email=email, website="https://buh.ru/"))


# --- form token ------------------------------------------------------------


def test_form_token_accepts_human_speed(cfg: Settings) -> None:
    token = leads_service.issue_form_token(cfg, now=1000)
    leads_service.check_form_token(token, cfg, now=1010)


def test_form_token_rejects_too_fast_submission(cfg: Settings) -> None:
    token = leads_service.issue_form_token(cfg, now=1000)
    with pytest.raises(LeadRejectedError, match="too fast"):
        leads_service.check_form_token(token, cfg, now=1001)


def test_form_token_rejects_expired(cfg: Settings) -> None:
    token = leads_service.issue_form_token(cfg, now=1000)
    with pytest.raises(LeadRejectedError, match="expired"):
        leads_service.check_form_token(token, cfg, now=1000 + 3601)


@pytest.mark.parametrize("token", ["garbage", "1000.abc.deadbeef", "x.y.z", ""])
def test_form_token_rejects_forged(cfg: Settings, token: str) -> None:
    with pytest.raises(LeadRejectedError, match="invalid"):
        leads_service.check_form_token(token, cfg, now=2000)


def test_form_token_rejects_tampered_timestamp(cfg: Settings) -> None:
    token = leads_service.issue_form_token(cfg, now=1000)
    _, nonce, sig = token.split(".")
    with pytest.raises(LeadRejectedError, match="invalid"):
        leads_service.check_form_token(f"900.{nonce}.{sig}", cfg, now=2000)


def test_content_checks() -> None:
    leads_service.check_content("Нужен бухгалтер, сайт https://shop.ru")
    with pytest.raises(LeadRejectedError, match="links"):
        leads_service.check_content("Купите http://a.ru http://b.ru www.c.ru")
    with pytest.raises(LeadRejectedError, match="Russian"):
        leads_service.check_content("cheap viagra best price buy now please")


def test_unsubscribe_token_is_case_insensitive_and_secret_bound(cfg: Settings) -> None:
    token = leads_service.unsubscribe_token("Info@Buh.ru", cfg)
    assert token == leads_service.unsubscribe_token("info@buh.ru", cfg)
    other = cfg.model_copy(update={"jwt_secret": "another-secret-long-enough-for-hmac"})
    assert token != leads_service.unsubscribe_token("info@buh.ru", other)
    assert leads_service.unsubscribe_url("info@buh.ru", cfg).startswith(
        "https://ozzb2b.com/unsubscribe?email=info%40buh.ru&token="
    )


# --- drafts and notifications ----------------------------------------------


def test_draft_carries_request_but_not_client_contacts(cfg: Settings) -> None:
    subject, body = leads_service.render_draft(_lead(), _provider(), cfg)
    assert "маркетплейс" in subject
    assert "Wildberries" in body
    assert "Казань" in body
    assert "до 15 000" in body
    assert "https://buh.ru/" in body
    assert "/unsubscribe?email=info%40buh.ru" in body
    assert "anna@client.ru" not in body
    assert "Анна" not in body


def test_draft_without_city_or_budget(cfg: Settings) -> None:
    _, body = leads_service.render_draft(_lead(city=None, budget=None), _provider(), cfg)
    assert "можно удалённо" in body
    assert "Бюджет" not in body


def test_admin_notification_links_to_review_page(cfg: Settings) -> None:
    lead = _lead(description="<script>alert(1)</script> бухгалтер")
    mail = leads_service.admin_notification(lead, 3, cfg)
    assert mail is not None
    assert mail.to == "owner@example.com"
    url = f"https://ozzb2b.com/admin/leads/{lead.id}"
    assert url in mail.body
    assert mail.html is not None and url in mail.html
    assert "<script>" not in mail.html
    assert "Черновиков писем подрядчикам: 3" in mail.body


def test_client_confirmation_does_not_echo_free_text(cfg: Settings) -> None:
    lead = _lead(description="Купите наш курс http://spam.example бухгалтер")
    mail = leads_service.client_confirmation(lead, cfg)
    assert mail.to == "anna@client.ru"
    assert "Анна" in mail.body
    assert "Казань" in mail.body
    assert "может и не найтись" in mail.body
    assert "spam.example" not in mail.body
    assert mail.reply_to == "owner@example.com"


def test_admin_notification_disabled_without_address(cfg: Settings) -> None:
    off = cfg.model_copy(update={"admin_notify_email": ""})
    assert leads_service.admin_notification(_lead(), 0, off) is None


# --- mailer ----------------------------------------------------------------


def test_build_message_headers(cfg: Settings) -> None:
    msg = mailer.build_message(
        OutgoingMail(
            to="info@buh.ru",
            subject="Тема",
            body="Текст",
            list_unsubscribe="https://ozzb2b.com/unsubscribe?x=1",
            html="<p>Текст</p>",
        ),
        cfg.model_copy(update={"mail_reply_to": "hello@ozzb2b.com"}),
    )
    assert msg["From"] == "ozzb2b <noreply@ozzb2b.com>"
    assert msg["Reply-To"] == "hello@ozzb2b.com"
    assert msg["List-Unsubscribe"] == "<https://ozzb2b.com/unsubscribe?x=1>"
    assert msg["Message-ID"].endswith("@ozzb2b.com>")
    assert msg.is_multipart()


async def test_send_mail_disabled_never_connects(
    cfg: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_: Any) -> None:
        raise AssertionError("must not connect")

    monkeypatch.setattr(mailer, "_send_sync", boom)
    await mailer.send_mail(OutgoingMail(to="a@b.ru", subject="s", body="b"), cfg)


async def test_send_mail_wraps_smtp_errors(cfg: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_: Any) -> None:
        raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    monkeypatch.setattr(mailer, "_send_sync", fail)
    on = cfg.model_copy(update={"mail_enabled": True})
    with pytest.raises(MailDeliveryError):
        await mailer.send_mail(OutgoingMail(to="a@b.ru", subject="s", body="b"), on)


async def test_send_quietly_swallows_delivery_errors(
    cfg: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail(*_: Any) -> None:
        raise MailDeliveryError("down")

    monkeypatch.setattr(mailer, "send_mail", fail)
    await leads_service.send_quietly(OutgoingMail(to="a@b.ru", subject="s", body="b"), cfg)


# --- HTTP ------------------------------------------------------------------


def _payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "category_slug": "marketplace-accounting",
        "description": "Нужен бухгалтер для ООО на Ozon, ОСНО, нужна помощь с НДС.",
        "contact_name": "Иван",
        "contact_email": "ivan@client.ru",
        "consent": True,
        "form_token": "1000.nonce.not-a-real-signature",
    }
    data.update(overrides)
    return data


def test_form_token_endpoint(client: TestClient) -> None:
    res = client.get("/leads/form-token")
    assert res.status_code == 200
    assert res.headers["cache-control"] == "no-store"
    assert res.json()["token"].count(".") == 2


def test_honeypot_pretends_success(client: TestClient) -> None:
    res = client.post("/leads", json=_payload(website="http://spam.example"))
    assert res.status_code == 201
    assert res.json() == {"ok": True}


def test_forged_token_is_rejected(client: TestClient) -> None:
    res = client.post("/leads", json=_payload())
    assert res.status_code == 422
    assert res.json()["detail"] == "invalid form token"


def test_consent_is_required(client: TestClient) -> None:
    res = client.post("/leads", json=_payload(consent=False))
    assert res.status_code == 422
    assert res.json()["detail"] == "consent required"


def test_unsubscribe_rejects_bad_token(client: TestClient) -> None:
    res = client.post(
        "/email/unsubscribe", json={"email": "info@buh.ru", "token": "deadbeefdeadbeef"}
    )
    assert res.status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/admin/leads"),
        ("GET", f"/admin/leads/{uuid.uuid4()}"),
        ("POST", f"/admin/leads/outreach/{uuid.uuid4()}/send"),
        ("POST", f"/admin/leads/{uuid.uuid4()}/outreach/bulk"),
    ],
)
def test_admin_lead_routes_require_auth(client: TestClient, method: str, path: str) -> None:
    assert client.request(method, path).status_code == 401
