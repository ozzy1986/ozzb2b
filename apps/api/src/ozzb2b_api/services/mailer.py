"""Plain-text e-mail over SMTP (Timeweb mailbox in production).

Uses the stdlib ``smtplib`` in a worker thread: we send a handful of
messages a day, so a dedicated async SMTP dependency isn't worth it. With
``mail_enabled=False`` (dev/test) messages are only logged.
"""

from __future__ import annotations

import asyncio
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

import structlog

from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.errors import ExternalServiceError

log = structlog.get_logger("ozzb2b_api.services.mailer")


class MailDeliveryError(ExternalServiceError):
    """SMTP rejected or could not deliver the message."""


@dataclass(frozen=True)
class OutgoingMail:
    to: str
    subject: str
    body: str
    reply_to: str | None = None
    list_unsubscribe: str | None = None
    html: str | None = None


def build_message(mail: OutgoingMail, cfg: Settings) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = cfg.mail_from
    msg["To"] = mail.to
    msg["Subject"] = mail.subject
    msg["Date"] = formatdate(localtime=True)
    domain = parseaddr(cfg.mail_from)[1].rpartition("@")[2] or "ozzb2b.com"
    msg["Message-ID"] = make_msgid(domain=domain)
    reply_to = mail.reply_to or cfg.mail_reply_to
    if reply_to:
        msg["Reply-To"] = reply_to
    if mail.list_unsubscribe:
        msg["List-Unsubscribe"] = f"<{mail.list_unsubscribe}>"
    msg.set_content(mail.body)
    if mail.html:
        msg.add_alternative(mail.html, subtype="html")
    return msg


def _send_sync(msg: EmailMessage, cfg: Settings) -> None:
    context = ssl.create_default_context()
    smtp: smtplib.SMTP
    if cfg.smtp_use_ssl:
        smtp = smtplib.SMTP_SSL(
            cfg.smtp_host, cfg.smtp_port, timeout=cfg.smtp_timeout_seconds, context=context
        )
    else:
        smtp = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=cfg.smtp_timeout_seconds)
    with smtp:
        if not cfg.smtp_use_ssl:
            smtp.starttls(context=context)
        if cfg.smtp_username:
            smtp.login(cfg.smtp_username, cfg.smtp_password)
        smtp.send_message(msg)


async def send_mail(mail: OutgoingMail, cfg: Settings | None = None) -> None:
    cfg = cfg or get_settings()
    msg = build_message(mail, cfg)
    if not cfg.mail_enabled:
        log.info("mail.skipped_disabled", to=mail.to, subject=mail.subject)
        return
    try:
        await asyncio.to_thread(_send_sync, msg, cfg)
    except (smtplib.SMTPException, OSError) as exc:
        log.warning("mail.send_failed", to=mail.to, error=str(exc))
        raise MailDeliveryError(f"mail delivery failed: {exc}") from exc
    log.info("mail.sent", to=mail.to, subject=mail.subject)
