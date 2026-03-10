from sqlalchemy import event
from sqlalchemy.orm import Session

from .models import AuditLog


def setup_immutability_listeners():
    @event.listens_for(Session, "before_flush")
    def prevent_audit_mutation(session: Session, flush_context, instances):
        # Interdire UPDATE
        for obj in session.dirty:
            if isinstance(obj, AuditLog):
                raise RuntimeError("AuditLog is immutable: updates are not allowed")

        # Interdire DELETE
        for obj in session.deleted:
            if isinstance(obj, AuditLog):
                raise RuntimeError("AuditLog is immutable: deletes are not allowed")