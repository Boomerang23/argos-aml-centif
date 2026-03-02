from sqlalchemy.orm import Session
from ..models import AuditLog

def log_audit(db: Session, case_id: int, action: str, details: str) -> None:
    db.add(AuditLog(case_id=case_id, action=action, details=details))
    db.commit()