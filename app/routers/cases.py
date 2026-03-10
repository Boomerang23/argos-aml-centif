from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..deps import get_db, get_current_user
from ..models import (
    Case,
    Party,
    CaseStatus,
    AuditLog,
    UserRole,
)
from ..schemas import (
    CaseCreate,
    CaseUpdate,
    CaseOut,
    PartyCreate,
    ComplianceDecisionIn,
    ComplianceDecisionOut,
)
from ..services.audit import log_audit
from ..services.scoring import apply_scoring

router = APIRouter(prefix="/cases", tags=["cases"])


def compute_case_status(c: Case) -> CaseStatus:
    """
    Règle simple V1 (complétude données transactionnelles):
    - DRAFT si des champs obligatoires manquent
    - ORANGE si tout est rempli (le scoring décidera ensuite GREEN/ORANGE/RED)
    """
    required = [
        c.reference,
        c.amount_fcfa,
        c.payment_mode,
        c.funds_origin,
        c.country_residence,
        c.profession,
    ]
    if any(v is None or (isinstance(v, str) and not v.strip()) for v in required):
        return CaseStatus.DRAFT
    return CaseStatus.ORANGE


@router.post("", response_model=CaseOut)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = Case(
        org_id=user.org_id,
        reference=payload.reference,
        amount_fcfa=payload.amount_fcfa,
        payment_mode=payload.payment_mode,
        funds_origin=payload.funds_origin,
        country_residence=payload.country_residence,
        profession=payload.profession,
        created_by_user_id=user.id,
    )

    base_status = compute_case_status(c)
    if base_status == CaseStatus.DRAFT:
        c.status = CaseStatus.DRAFT
    else:
        apply_scoring(c, pep=False)

    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Reference already exists")

    db.refresh(c)
    log_audit(
        db,
        c.id,
        "CASE_CREATED",
        f"Case {c.reference} created (risk_score={c.risk_score} status={c.status})",
    )
    db.commit()
    return c


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(403, "Not allowed")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(c, k, v)

    old_status = c.status
    old_score = c.risk_score

    base_status = compute_case_status(c)
    if base_status == CaseStatus.DRAFT:
        c.status = CaseStatus.DRAFT
        c.risk_score = 0
        c.risk_details = None
    else:
        apply_scoring(c, pep=False)

    db.commit()
    db.refresh(c)

    log_audit(
        db,
        c.id,
        "CASE_UPDATED",
        f"Fields updated: {list(data.keys())} | risk_score {old_score}->{c.risk_score} | status {old_status}->{c.status}",
    )
    db.commit()
    return c

@router.get("/{case_id}/audit")
def list_case_audit(case_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(403, "Not allowed")

    rows = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(AuditLog.id.desc())
        .all()
    )

    return [
        {
            "id": a.id,
            "action": a.action,
            "details": a.details,
            "prev_hash": a.prev_hash,
            "hash": a.hash,
            "created_at": a.created_at,
        }
        for a in rows
    ]

@router.post("/{case_id}/parties")
def add_party(
    case_id: int,
    payload: PartyCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(403, "Not allowed")

    p = Party(case_id=case_id, **payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)

    log_audit(
        db,
        case_id,
        "PARTY_ADDED",
        f"{payload.party_type}: {payload.last_name} {payload.first_name}",
    )
    db.commit()
    return {"ok": True, "party_id": p.id}


@router.get("/{case_id}/parties")
def list_parties(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(403, "Not allowed")

    parties = (
        db.query(Party)
        .filter(Party.case_id == case_id)
        .order_by(Party.id.asc())
        .all()
    )

    return [
        {
            "id": p.id,
            "party_type": p.party_type.value if hasattr(p.party_type, "value") else str(p.party_type),
            "last_name": p.last_name,
            "first_name": p.first_name,
            "birth_date": str(p.birth_date) if p.birth_date else None,
            "nationality": p.nationality,
            "address": p.address,
            "email": p.email,
            "phone": p.phone,
            "id_number": p.id_number,
        }
        for p in parties
    ]


@router.get("", response_model=list[CaseOut])
def list_cases(
    status: CaseStatus | None = None,
    created_by_user_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    - ADMIN / COMPLIANCE_OFFICER : voient tous les cases de leur org
    - AGENT : voit seulement ses propres cases
    + filtres simples
    """
    q = select(Case).where(Case.org_id == user.org_id)

    if user.role == UserRole.AGENT:
        q = q.where(Case.created_by_user_id == user.id)

    if status is not None:
        q = q.where(Case.status == status)

    if created_by_user_id is not None:
        if user.role == UserRole.AGENT:
            raise HTTPException(status_code=403, detail="Not allowed")
        q = q.where(Case.created_by_user_id == created_by_user_id)

    cases = db.scalars(q.order_by(Case.updated_at.desc())).all()
    return cases


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(403, "Not allowed")

    return c

@router.post("/{case_id}/compliance-decision")
def compliance_decision(
    case_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    decision = payload.get("decision")
    comment = payload.get("comment")

    if decision not in ["VALIDATED", "ESCALATED", "REJECTED"]:
        raise HTTPException(400, "Invalid decision")

    c.compliance_decision = decision
    c.compliance_comment = comment
    c.date_validation = datetime.utcnow()
    c.validated_by_user_id = user.id

    db.add(c)
    db.commit()

    return {
        "status": "ok",
        "decision": decision,
    }


@router.post("/{case_id}/compliance-decision", response_model=ComplianceDecisionOut)
def set_compliance_decision(
    case_id: int,
    payload: ComplianceDecisionIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role not in [UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER]:
        raise HTTPException(status_code=403, detail="Not allowed")

    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    if c.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    c.compliance_decision = payload.decision
    c.compliance_comment = payload.comment
    c.validated_by_user_id = user.id
    c.date_validation = datetime.now(timezone.utc)

    db.commit()
    db.refresh(c)

    log_audit(
        db,
        case_id,
        "COMPLIANCE_DECISION",
        f"decision={payload.decision.value} by={user.email}",
    )
    db.commit()

    return {
        "ok": True,
        "case_id": case_id,
        "compliance_decision": c.compliance_decision,
        "compliance_comment": c.compliance_comment,
        "validated_by_user_id": c.validated_by_user_id,
        "date_validation": c.date_validation,
    }