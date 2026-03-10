from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Case, Party, Document, DocumentType, CaseStatus


REQUIRED_DOCS = {DocumentType.ID, DocumentType.PROOF_ADDRESS}


def case_has_required_fields(c: Case) -> bool:
    required = [
        c.reference,
        c.amount_fcfa,
        c.payment_mode,
        c.funds_origin,
        c.country_residence,
        c.profession,
    ]
    return not any(v is None or (isinstance(v, str) and not v.strip()) for v in required)


def build_kyc_checklist(db: Session, case_id: int) -> dict:
    """
    Retourne une checklist KYC:
    - parties présentes
    - docs présents par partie
    """
    parties = db.scalars(select(Party).where(Party.case_id == case_id)).all()
    docs = db.scalars(select(Document).where(Document.case_id == case_id)).all()

    docs_by_party: dict[int, set] = {}
    for d in docs:
        if d.party_id is None:
            continue
        docs_by_party.setdefault(d.party_id, set()).add(d.doc_type)

    checklist = {
        "case_id": case_id,
        "parties": [],
        "missing": [],
        "is_complete": True,
    }

    if not parties:
        checklist["is_complete"] = False
        checklist["missing"].append("NO_PARTIES")

    for p in parties:
        present = docs_by_party.get(p.id, set())
        missing = [dt.value for dt in REQUIRED_DOCS if dt not in present]
        checklist["parties"].append(
            {
                "party_id": p.id,
                "party_type": p.party_type.value,
                "name": f"{p.last_name} {p.first_name}",
                "present_docs": [dt.value for dt in present],
                "missing_docs": missing,
            }
        )
        if missing:
            checklist["is_complete"] = False

    return checklist


def recompute_case_status_with_kyc(db: Session, case: Case) -> dict:
    """
    Règle simple V1 (alignée cahier):
    - Si champs transactionnels incomplets => DRAFT
    - Sinon si KYC incomplet => ORANGE (dossier incomplet / vigilance normale)
    - Sinon: on garde le status actuel (qui vient du scoring/screening)
      mais on ne downgrade jamais un RED.
    """
    checklist = build_kyc_checklist(db, case.id)

    if not case_has_required_fields(case):
        case.status = CaseStatus.DRAFT
        return checklist

    if not checklist["is_complete"]:
        # On ne downgrade pas RED
        if case.status != CaseStatus.RED:
            case.status = CaseStatus.ORANGE
        return checklist

    # KYC complet: si pas RED, on laisse le scoring décider (GREEN/ORANGE)
    # (si ton scoring a déjà mis ORANGE/ GREEN, on ne touche pas)
    return checklist