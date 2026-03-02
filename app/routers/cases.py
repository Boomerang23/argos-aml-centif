from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..deps import get_db, get_current_user
from ..models import Case, Party, CaseStatus
from ..schemas import CaseCreate, PartyCreate, CaseOut
from ..services.audit import log_audit
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("", response_model=CaseOut)
def create_case(payload: CaseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = Case(**payload.model_dump(), created_by_user_id=user.id, status=CaseStatus.ORANGE)
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Reference already exists")
    db.refresh(c)
    log_audit(db, c.id, "CASE_CREATED", f"Case {c.reference} created")
    return CaseOut(
    id=c.id,
    reference=c.reference,
    status=c.status,
    amount_fcfa=c.amount_fcfa,
    payment_mode=c.payment_mode,
    country_residence=c.country_residence,
    funds_origin=c.funds_origin,
)

@router.post("/{case_id}/parties")
def add_party(case_id: int, payload: PartyCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")
    p = Party(case_id=case_id, **payload.model_dump())
    db.add(p)
    db.commit()
    log_audit(db, case_id, "PARTY_ADDED", f"{payload.party_type} {payload.full_name}")
    return {"ok": True, "party_id": p.id}

@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cases = db.scalars(select(Case).order_by(Case.updated_at.desc())).all()
    return [
    CaseOut(
        id=c.id,
        reference=c.reference,
        status=c.status,
        amount_fcfa=c.amount_fcfa,
        payment_mode=c.payment_mode,
        country_residence=c.country_residence,
        funds_origin=c.funds_origin,
    )
    for c in cases
]