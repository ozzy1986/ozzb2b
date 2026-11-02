"""leads, outreach drafts and e-mail suppressions

Revision ID: 0005_leads_outreach
Revises: 0004_provider_claims
Create Date: 2026-11-03 12:00:00
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision: str = "0005_leads_outreach"
down_revision: str | Sequence[str] | None = "0004_provider_claims"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column[datetime]]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "city_id",
            sa.Integer(),
            sa.ForeignKey("cities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("budget", sa.String(length=120), nullable=True),
        sa.Column("contact_name", sa.String(length=120), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=64), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'new'"),
        ),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_leads_category_id", "leads", ["category_id"])
    op.create_index("ix_leads_status", "leads", ["status"])

    op.create_table(
        "outreach_messages",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lead_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("lead_id", "provider_id", name="uq_outreach_lead_provider"),
    )
    op.create_index("ix_outreach_messages_lead_id", "outreach_messages", ["lead_id"])
    op.create_index("ix_outreach_messages_provider_id", "outreach_messages", ["provider_id"])
    op.create_index("ix_outreach_messages_status", "outreach_messages", ["status"])

    op.create_table(
        "email_suppressions",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("email", name="uq_email_suppressions_email"),
    )


def downgrade() -> None:
    op.drop_table("email_suppressions")
    op.drop_index("ix_outreach_messages_status", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_provider_id", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_lead_id", table_name="outreach_messages")
    op.drop_table("outreach_messages")
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_index("ix_leads_category_id", table_name="leads")
    op.drop_table("leads")
