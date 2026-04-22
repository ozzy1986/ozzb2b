"""normalize enum columns to store lowercase values

Revision ID: 0002_enum_values
Revises: 0001_baseline
Create Date: 2026-04-22 09:15:00
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_enum_values"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE providers SET status = lower(status)")
    op.execute("UPDATE users SET role = lower(role)")


def downgrade() -> None:
    op.execute("UPDATE providers SET status = upper(status)")
    op.execute("UPDATE users SET role = upper(role)")
