from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

from .models import CaseStatus, PartyType, DocumentType, ComplianceDecision


# ---------- AUTH ----------
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ---------- CASES ----------
class CaseCreate(BaseModel):
    # obligatoire
    reference: str

    # champs transactionnels (cahier)
    amount_fcfa: Optional[int] = None
    payment_mode: Optional[str] = None
    funds_origin: Optional[str] = None
    country_residence: Optional[str] = None
    profession: Optional[str] = None


class CaseUpdate(BaseModel):
    amount_fcfa: Optional[int] = None
    payment_mode: Optional[str] = None
    funds_origin: Optional[str] = None
    country_residence: Optional[str] = None
    profession: Optional[str] = None


class CaseOut(BaseModel):
    id: int
    reference: str
    status: CaseStatus

    amount_fcfa: Optional[int] = None
    payment_mode: Optional[str] = None
    funds_origin: Optional[str] = None
    country_residence: Optional[str] = None
    profession: Optional[str] = None

    risk_score: int
    compliance_decision: Optional[ComplianceDecision] = None
    compliance_comment: Optional[str] = None
    date_validation: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- PARTIES ----------
class PartyCreate(BaseModel):
    party_type: PartyType

    # cahier: nom, prénoms, date naissance, nationalité, adresse, email, téléphone
    last_name: str
    first_name: str
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # optionnel
    id_number: Optional[str] = None


# ---------- SCREENING ----------
class ScreeningIn(BaseModel):
    query: str


class ScreeningOut(BaseModel):
    id: int
    query: str
    provider: str
    risk_flag: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ComplianceDecisionIn(BaseModel):
    decision: ComplianceDecision
    comment: str | None = None


class ComplianceDecisionOut(BaseModel):
    ok: bool
    case_id: int
    compliance_decision: ComplianceDecision | None
    compliance_comment: str | None
    validated_by_user_id: int | None
    date_validation: datetime | None