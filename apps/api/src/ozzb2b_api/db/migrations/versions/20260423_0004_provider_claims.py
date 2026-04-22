"""provider_claims table for claim-your-company flow

Revision ID: 0004_provider_claims
Revises: 0003_chat_tables
Create Date: 2026-04-23 20:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision: str = "0004_provider_claims"
down_revision: str | Sequence[str] | None = "0003_chat_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_claims",
        sa.Column("id", PgUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "provider_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            PgUUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "method",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'meta_tag'"),
        ),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_reason", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_provider_claims_provider_id", "provider_claims", ["provider_id"])
    op.create_index("ix_provider_claims_user_id", "provider_claims", ["user_id"])
    op.create_index("ix_provider_claims_status", "provider_claims", ["status"])
    op.create_index("ix_provider_claims_token_hash", "provider_claims", ["token_hash"])
    # Only one verified claim per provider at a time; enforced at the DB layer
    # so race conditions around simultaneous verifications can't corrupt state.
    op.create_index(
        "uq_provider_claims_verified_per_provider",
        "provider_claims",
        ["provider_id"],
        unique=True,
        postgresql_where=sa.text("status = 'verified'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_provider_claims_verified_per_provider", table_name="provider_claims"
    )
    op.drop_index("ix_provider_claims_token_hash", table_name="provider_claims")
    op.drop_index("ix_provider_claims_status", table_name="provider_claims")
    op.drop_index("ix_provider_claims_user_id", table_name="provider_claims")
    op.drop_index("ix_provider_claims_provider_id", table_name="provider_claims")
    op.drop_table("provider_claims")
