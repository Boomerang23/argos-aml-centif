from pydantic import BaseModel, EmailStr
from typing import Optional, List
from .models import CaseStatus, PartyType, DocumentType

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class CaseCreate(BaseModel):
    reference: str
    amount_fcfa: Optional[int] = None
    payment_mode: Optional[str] = None
    country_residence: Optional[str] = None
    funds_origin: Optional[str] = None

class PartyCreate(BaseModel):
    party_type: PartyType
    full_name: str
    id_number: Optional[str] = None
    nationality: Optional[str] = None

class CaseOut(BaseModel):
    id: int
    reference: str
    status: CaseStatus
    amount_fcfa: Optional[int]
    payment_mode: Optional[str]
    country_residence: Optional[str]
    funds_origin: Optional[str]

class ScreeningIn(BaseModel):
    query: str

class ScreeningOut(BaseModel):
    id: int
    query: str
    provider: str
    risk_flag: bool
    created_at: str