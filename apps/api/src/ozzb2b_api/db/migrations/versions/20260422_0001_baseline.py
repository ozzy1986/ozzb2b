"""baseline: core domain schema (users, geo, categories, legal forms, providers)

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-22 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- extensions ---------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent"')

    # --- users ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="client"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- refresh tokens ------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_refresh_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])

    # --- geo -----------------------------------------------------------------
    op.create_table(
        "countries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("code", name="uq_countries_code"),
        sa.UniqueConstraint("slug", name="uq_countries_slug"),
    )

    op.create_table(
        "cities",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("country_id", sa.Integer, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("region", sa.String(128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
            name="fk_cities_country_id_countries",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("country_id", "slug", name="uq_cities_country_id_slug"),
    )
    op.create_index("ix_cities_country_id", "cities", ["country_id"])

    # --- legal forms ---------------------------------------------------------
    op.create_table(
        "legal_forms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("country_id", sa.Integer, nullable=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["countries.id"],
            name="fk_legal_forms_country_id_countries",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("country_id", "code", name="uq_legal_forms_country_id_code"),
        sa.UniqueConstraint("country_id", "slug", name="uq_legal_forms_country_id_slug"),
    )
    op.create_index("ix_legal_forms_country_id", "legal_forms", ["country_id"])

    # --- categories ----------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("parent_id", sa.Integer, nullable=True),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name="fk_categories_parent_id_categories",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    # --- providers -----------------------------------------------------------
    op.create_table(
        "providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("country_id", sa.Integer, nullable=True),
        sa.Column("city_id", sa.Integer, nullable=True),
        sa.Column("legal_form_id", sa.Integer, nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("registration_number", sa.String(64), nullable=True),
        sa.Column("tax_id", sa.String(64), nullable=True),
        sa.Column("year_founded", sa.Integer, nullable=True),
        sa.Column("employee_count_range", sa.String(32), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("source_id", sa.String(128), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="published"),
        sa.Column("is_claimed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("claimed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "meta",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("search_document", postgresql.TSVECTOR, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["country_id"], ["countries.id"], name="fk_providers_country_id_countries", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.id"], name="fk_providers_city_id_cities", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["legal_form_id"],
            ["legal_forms.id"],
            name="fk_providers_legal_form_id_legal_forms",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["claimed_by_user_id"],
            ["users.id"],
            name="fk_providers_claimed_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("slug", name="uq_providers_slug"),
        sa.UniqueConstraint("source", "source_id", name="uq_providers_source_source_id"),
    )
    op.create_index("ix_providers_slug", "providers", ["slug"])
    op.create_index("ix_providers_country_id", "providers", ["country_id"])
    op.create_index("ix_providers_city_id", "providers", ["city_id"])
    op.create_index("ix_providers_legal_form_id", "providers", ["legal_form_id"])
    op.create_index("ix_providers_status", "providers", ["status"])
    op.create_index("ix_providers_source", "providers", ["source"])
    op.create_index("ix_providers_source_id", "providers", ["source_id"])
    op.create_index("ix_providers_registration_number", "providers", ["registration_number"])
    op.create_index("ix_providers_tax_id", "providers", ["tax_id"])
    op.create_index(
        "ix_providers_search_document_gin",
        "providers",
        ["search_document"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_providers_display_name_trgm",
        "providers",
        ["display_name"],
        postgresql_using="gin",
        postgresql_ops={"display_name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_providers_legal_name_trgm",
        "providers",
        ["legal_name"],
        postgresql_using="gin",
        postgresql_ops={"legal_name": "gin_trgm_ops"},
    )

    # --- provider <-> categories m2m -----------------------------------------
    op.create_table(
        "provider_categories",
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["providers.id"],
            name="fk_provider_categories_provider_id_providers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_provider_categories_category_id_categories",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("provider_id", "category_id", name="pk_provider_categories"),
    )
    op.create_index("ix_provider_categories_category_id", "provider_categories", ["category_id"])

    # --- FTS trigger to keep search_document in sync -------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION providers_search_document_update()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.search_document :=
              setweight(to_tsvector('simple', unaccent(coalesce(NEW.display_name, ''))), 'A') ||
              setweight(to_tsvector('simple', unaccent(coalesce(NEW.legal_name,   ''))), 'A') ||
              setweight(to_tsvector('simple', unaccent(coalesce(NEW.description,  ''))), 'B') ||
              setweight(to_tsvector('simple', unaccent(coalesce(NEW.address,      ''))), 'C');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_providers_search_document
        BEFORE INSERT OR UPDATE OF display_name, legal_name, description, address
        ON providers
        FOR EACH ROW EXECUTE FUNCTION providers_search_document_update();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_providers_search_document ON providers")
    op.execute("DROP FUNCTION IF EXISTS providers_search_document_update()")

    op.drop_index("ix_provider_categories_category_id", table_name="provider_categories")
    op.drop_table("provider_categories")

    for ix in (
        "ix_providers_legal_name_trgm",
        "ix_providers_display_name_trgm",
        "ix_providers_search_document_gin",
        "ix_providers_tax_id",
        "ix_providers_registration_number",
        "ix_providers_source_id",
        "ix_providers_source",
        "ix_providers_status",
        "ix_providers_legal_form_id",
        "ix_providers_city_id",
        "ix_providers_country_id",
        "ix_providers_slug",
    ):
        op.drop_index(ix, table_name="providers")
    op.drop_table("providers")

    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_legal_forms_country_id", table_name="legal_forms")
    op.drop_table("legal_forms")

    op.drop_index("ix_cities_country_id", table_name="cities")
    op.drop_table("cities")

    op.drop_table("countries")

    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
