import enum
from datetime import datetime, date

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .db import Base


# -------------------------
# ENUMS
# -------------------------

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    AGENT = "AGENT"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"


class CaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ORANGE = "ORANGE"
    RED = "RED"
    GREEN = "GREEN"


class ComplianceDecision(str, enum.Enum):
    VALIDATED = "VALIDATED"
    ESCALATED = "ESCALATED"
    REJECTED = "REJECTED"


class PartyType(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"


class DocumentType(str, enum.Enum):
    ID = "ID"
    PROOF_ADDRESS = "PROOF_ADDRESS"
    OTHER = "OTHER"


# -------------------------
# TABLES
# -------------------------

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    organization = relationship("Organization")

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.AGENT)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # multi-agence
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    organization = relationship("Organization")

    reference: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.DRAFT)

    amount_fcfa: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    funds_origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country_residence: Mapped[str | None] = mapped_column(String(64), nullable=True)
    profession: Mapped[str | None] = mapped_column(String(128), nullable=True)

    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    compliance_decision: Mapped[ComplianceDecision | None] = mapped_column(
        Enum(ComplianceDecision), nullable=True
    )
    compliance_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    validated_by = relationship("User", foreign_keys=[validated_by_user_id])
    date_validation: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parties = relationship("Party", back_populates="case", cascade="all, delete-orphan")
    screenings = relationship("Screening", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    audits = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")


class Party(Base):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="parties")

    party_type: Mapped[PartyType] = mapped_column(Enum(PartyType))

    last_name: Mapped[str] = mapped_column(String(128))
    first_name: Mapped[str] = mapped_column(String(128))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    id_number: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="documents")

    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"), nullable=True)

    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="screenings")

    query: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(64), default="OpenSanctions")

    result_json: Mapped[str] = mapped_column(Text)
    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="audits")

    action: Mapped[str] = mapped_column(String(128))
    details: Mapped[str] = mapped_column(Text)

    # ✅ immutabilité par chaînage
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )