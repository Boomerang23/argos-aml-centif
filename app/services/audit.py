import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import AuditLog


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def log_audit(db: Session, case_id: int, action: str, details: str) -> AuditLog:
    # Récupère le dernier hash du case
    last = db.scalars(
        select(AuditLog)
        .where(AuditLog.case_id == case_id)
        .order_by(AuditLog.id.desc())
        .limit(1)
    ).first()

    prev_hash = last.hash if last else None

    # payload stable
    payload = f"{case_id}|{action}|{details}|{prev_hash or ''}"
    h = _sha256_hex(payload)

    entry = AuditLog(
        case_id=case_id,
        action=action,
        details=details,
        prev_hash=prev_hash,
        hash=h,
    )

    db.add(entry)
    db.flush()  # crée l'id sans commit forcé
    return entry