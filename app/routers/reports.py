from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import Case, UserRole
from ..services.pdf_report import generate_case_pdf
from ..services.audit import log_audit

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/cases/{case_id}/pdf")
def download_case_pdf(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.get(Case, case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    # ✅ Sécurité multi-agence
    if c.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ AGENT: seulement ses propres dossiers
    if user.role == UserRole.AGENT and c.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    path = generate_case_pdf(db, case_id)

    log_audit(db, case_id, "EXPORT_PDF", f"PDF generated: {path}")
    db.commit()

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.split("/")[-1].split("\\")[-1],
    )