from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..deps import get_db, get_current_user
from ..models import Case, CaseStatus, ComplianceDecision, UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Base query: org only
    base = select(Case).where(Case.org_id == user.org_id)

    # AGENT: seulement ses dossiers
    if user.role == UserRole.AGENT:
        base = base.where(Case.created_by_user_id == user.id)

    # Total
    total = db.scalar(select(func.count()).select_from(base.subquery()))

    # Comptage par statut
    def count_status(st: CaseStatus) -> int:
        q = select(func.count()).select_from(
            base.where(Case.status == st).subquery()
        )
        return int(db.scalar(q) or 0)

    draft = count_status(CaseStatus.DRAFT)
    orange = count_status(CaseStatus.ORANGE)
    green = count_status(CaseStatus.GREEN)
    red = count_status(CaseStatus.RED)

    # Décisions conformité
    def count_decision(dec: ComplianceDecision) -> int:
        q = select(func.count()).select_from(
            base.where(Case.compliance_decision == dec).subquery()
        )
        return int(db.scalar(q) or 0)

    validated = count_decision(ComplianceDecision.VALIDATED)
    escalated = count_decision(ComplianceDecision.ESCALATED)
    rejected = count_decision(ComplianceDecision.REJECTED)

    return {
        "scope": "org" if user.role != UserRole.AGENT else "agent",
        "total_cases": int(total or 0),
        "by_status": {
            "DRAFT": draft,
            "ORANGE": orange,
            "GREEN": green,
            "RED": red,
        },
        "alerts": {
            "red_cases": red,
            "draft_incomplete": draft,
        },
        "compliance_decisions": {
            "VALIDATED": validated,
            "ESCALATED": escalated,
            "REJECTED": rejected,
        },
    }