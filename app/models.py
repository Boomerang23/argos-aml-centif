import enum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .db import Base

class CaseStatus(str, enum.Enum):
    GREEN = "GREEN"
    ORANGE = "ORANGE"
    RED = "RED"

class PartyType(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"

class DocumentType(str, enum.Enum):
    ID = "ID"
    PROOF_ADDRESS = "PROOF_ADDRESS"
    OTHER = "OTHER"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.ORANGE)
    amount_fcfa: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)  # CASH, BANK, MIXED...
    country_residence: Mapped[str | None] = mapped_column(String(64), nullable=True)
    funds_origin: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by = relationship("User")

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

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
    full_name: Mapped[str] = mapped_column(String(255))
    id_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(64), nullable=True)

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="documents")

    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"), nullable=True)
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))  # path in S3
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Screening(Base):
    __tablename__ = "screenings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="screenings")

    query: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(64), default="OpenSanctions")
    result_json: Mapped[str] = mapped_column(Text)  # store raw response (or summarized)
    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    case = relationship("Case", back_populates="audits")

    action: Mapped[str] = mapped_column(String(128))
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())