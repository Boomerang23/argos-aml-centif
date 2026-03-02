from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..deps import get_db, get_current_user
from ..models import Case
from sqlalchemy import select
from ..services.pdf_report import build_case_pdf
from ..services.audit import log_audit

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/cases/{case_id}/pdf")
def export_case_pdf(case_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    case_dict = {
        "reference": c.reference,
        "status": c.status.value,
        "amount_fcfa": c.amount_fcfa,
        "payment_mode": c.payment_mode,
        "country_residence": c.country_residence,
        "funds_origin": c.funds_origin,
        "parties": [
            {"party_type": p.party_type.value, "full_name": p.full_name, "id_number": p.id_number, "nationality": p.nationality}
            for p in c.parties
        ],
        "screenings": [
            {"provider": s.provider, "query": s.query, "risk_flag": s.risk_flag, "created_at": s.created_at.isoformat()}
            for s in c.screenings
        ],
    }

    pdf, sha = build_case_pdf(case_dict)
    log_audit(db, case_id, "REPORT_EXPORTED", f"sha256={sha}")

    headers = {
        "Content-Disposition": f'attachment; filename="dossier_centif_{c.reference}.pdf"',
        "X-Report-SHA256": sha,
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)