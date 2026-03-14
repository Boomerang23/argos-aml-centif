"""initial schema

Revision ID: 281096ac5de8
Revises:
Create Date: 2026-03-13 23:23:52.199977

Initial schema: organizations, users, cases, parties, documents, screenings,
audit_logs. Uses PostgreSQL-native ENUMs when dialect is postgresql; SQLite
uses string columns. For a DB that already has tables (e.g. from create_all),
run `alembic stamp head` instead of upgrade.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.models import (
    UserRole,
    CaseStatus,
    ComplianceDecision,
    PartyType,
    DocumentType,
)


# revision identifiers, used by Alembic.
revision: str = "281096ac5de8"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # PostgreSQL: create enum types; SQLite uses CHECK/string
    if is_pg:
        userrole = sa.Enum(
            UserRole, name="userrole", create_constraint=True
        )
        casestatus = sa.Enum(
            CaseStatus, name="casestatus", create_constraint=True
        )
        compliancedecision = sa.Enum(
            ComplianceDecision,
            name="compliancedecision",
            create_constraint=True,
        )
        partytype = sa.Enum(
            PartyType, name="partytype", create_constraint=True
        )
        documenttype = sa.Enum(
            DocumentType, name="documenttype", create_constraint=True
        )
        userrole.create(bind, checkfirst=True)
        casestatus.create(bind, checkfirst=True)
        compliancedecision.create(bind, checkfirst=True)
        partytype.create(bind, checkfirst=True)
        documenttype.create(bind, checkfirst=True)

    # Enum type references for create_table (PostgreSQL uses type name)
    role_col = (
        sa.Enum("ADMIN", "AGENT", "COMPLIANCE_OFFICER", name="userrole")
        if is_pg
        else sa.String(32)
    )
    status_col = (
        sa.Enum("DRAFT", "ORANGE", "RED", "GREEN", name="casestatus")
        if is_pg
        else sa.String(32)
    )
    decision_col = (
        sa.Enum("VALIDATED", "ESCALATED", "REJECTED", name="compliancedecision")
        if is_pg
        else sa.String(32)
    )
    party_type_col = (
        sa.Enum("BUYER", "SELLER", name="partytype") if is_pg else sa.String(32)
    )
    doc_type_col = (
        sa.Enum("ID", "PROOF_ADDRESS", "OTHER", name="documenttype")
        if is_pg
        else sa.String(32)
    )

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organizations_name"), "organizations", ["name"], unique=True
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("role", role_col, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_org_id"), "users", ["org_id"], unique=False)

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("reference", sa.String(length=64), nullable=True),
        sa.Column("status", status_col, nullable=True),
        sa.Column("amount_fcfa", sa.Integer(), nullable=True),
        sa.Column("payment_mode", sa.String(length=64), nullable=True),
        sa.Column("funds_origin", sa.String(length=255), nullable=True),
        sa.Column("country_residence", sa.String(length=64), nullable=True),
        sa.Column("profession", sa.String(length=128), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("risk_details", sa.Text(), nullable=True),
        sa.Column("compliance_decision", decision_col, nullable=True),
        sa.Column("compliance_comment", sa.Text(), nullable=True),
        sa.Column("validated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "date_validation", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"],),
        sa.ForeignKeyConstraint(
            ["validated_by_user_id"], ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cases_org_id"), "cases", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_cases_reference"), "cases", ["reference"], unique=True
    )

    op.create_table(
        "parties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("party_type", party_type_col, nullable=True),
        sa.Column("last_name", sa.String(length=128), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("nationality", sa.String(length=64), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("id_number", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_parties_case_id"), "parties", ["case_id"], unique=False
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("party_id", sa.Integer(), nullable=True),
        sa.Column("doc_type", doc_type_col, nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"],),
        sa.ForeignKeyConstraint(["party_id"], ["parties.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_documents_case_id"), "documents", ["case_id"], unique=False
    )

    op.create_table(
        "screenings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("query", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("risk_flag", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_screenings_case_id"), "screenings", ["case_id"], unique=False
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("prev_hash", sa.String(length=64), nullable=True),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_case_id"),
        "audit_logs",
        ["case_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_audit_logs_case_id"), table_name="audit_logs"
    )
    op.drop_table("audit_logs")
    op.drop_index(
        op.f("ix_screenings_case_id"), table_name="screenings"
    )
    op.drop_table("screenings")
    op.drop_index(
        op.f("ix_documents_case_id"), table_name="documents"
    )
    op.drop_table("documents")
    op.drop_index(op.f("ix_parties_case_id"), table_name="parties")
    op.drop_table("parties")
    op.drop_index(op.f("ix_cases_reference"), table_name="cases")
    op.drop_index(op.f("ix_cases_org_id"), table_name="cases")
    op.drop_table("cases")
    op.drop_index(op.f("ix_users_org_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(
        op.f("ix_organizations_name"), table_name="organizations"
    )
    op.drop_table("organizations")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="userrole").drop(bind, checkfirst=True)
        sa.Enum(name="casestatus").drop(bind, checkfirst=True)
        sa.Enum(name="compliancedecision").drop(bind, checkfirst=True)
        sa.Enum(name="partytype").drop(bind, checkfirst=True)
        sa.Enum(name="documenttype").drop(bind, checkfirst=True)
