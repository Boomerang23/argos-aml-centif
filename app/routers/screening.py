import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db, get_current_user
from ..models import Case, Screening, CaseStatus
from ..schemas import ScreeningIn
from ..services.screening import opensanctions_search, detect_risk
from ..services.audit import log_audit

router = APIRouter(prefix="/screening", tags=["screening"])

@router.post("/cases/{case_id}")
async def run_screening(case_id: int, payload: ScreeningIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    resp = await opensanctions_search(payload.query)
    risk = detect_risk(resp)

    s = Screening(case_id=case_id, query=payload.query, result_json=json.dumps(resp), risk_flag=risk)
    db.add(s)

    # Statut simple MVP
    c.status = CaseStatus.RED if risk else CaseStatus.ORANGE  # ORANGE tant que docs incomplets/validation
    db.commit()

    log_audit(db, case_id, "SCREENING_RUN", f"query={payload.query} risk={risk}")
    return {"ok": True, "risk_flag": risk, "provider": "OpenSanctions", "raw": resp}