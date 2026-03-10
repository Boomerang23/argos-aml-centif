from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import Case, Screening, UserRole
from ..schemas import ScreeningIn
from ..services.screening import run_screening
from ..services.scoring import apply_scoring
from ..services.audit import log_audit

router = APIRouter(prefix="/screening", tags=["screening"])


@router.get("/cases/{case_id}")
def list_screenings(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    # ✅ Multi-agence: interdit accès cross-org
    if c.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ AGENT: seulement ses dossiers
    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    rows = (
        db.query(Screening)
        .filter(Screening.case_id == case_id)
        .order_by(Screening.created_at.desc())
        .all()
    )

    return [
        {
            "id": s.id,
            "query": s.query,
            "provider": s.provider,
            "risk_flag": s.risk_flag,
            "created_at": s.created_at,
            "result_json": s.result_json,
        }
        for s in rows
    ]


@router.post("/cases/{case_id}")
async def screening_case(
    case_id: int,
    payload: ScreeningIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    # ✅ Multi-agence: interdit accès cross-org
    if c.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ AGENT: seulement ses dossiers
    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 1) appel provider
    result = await run_screening(payload.query)
    risk_flag = bool(result.get("risk_flag", False))

    # 2) stockage screening
    s = Screening(
        case_id=case_id,
        query=payload.query,
        provider=result.get("provider", "OpenSanctions"),
        result_json=result.get("result_json", "{}"),
        risk_flag=risk_flag,
    )
    db.add(s)

    # 3) scoring
    apply_scoring(c, pep=risk_flag)

    db.commit()
    db.refresh(s)
    db.refresh(c)

    log_audit(db, case_id, "SCREENING_DONE", f"provider={s.provider} risk_flag={risk_flag}")
    log_audit(db, case_id, "SCORING_APPLIED", f"risk_score={c.risk_score} status={c.status}")
    db.commit()

    return {
        "ok": True,
        "screening_id": s.id,
        "risk_flag": risk_flag,
        "case_status": c.status,
        "risk_score": c.risk_score,
    }