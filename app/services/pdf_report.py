import os
import json
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Case, Party, Document, Screening, AuditLog
from ..services.kyc_checklist import build_kyc_checklist


def _safe(s: str | None) -> str:
    return (s or "").strip()


def _draw_title(c: canvas.Canvas, text: str, y: float) -> float:
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, text)
    return y - 8 * mm


def _draw_section(c: canvas.Canvas, title: str, y: float) -> float:
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, title)
    return y - 6 * mm


def _draw_kv(c: canvas.Canvas, k: str, v: str, y: float) -> float:
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, f"{k}:")
    c.setFont("Helvetica", 9)
    c.drawString(60 * mm, y, v)
    return y - 5 * mm


def _new_page_if_needed(c: canvas.Canvas, y: float) -> float:
    if y < 20 * mm:
        c.showPage()
        return 280 * mm
    return y


def generate_case_pdf(db: Session, case_id: int, output_dir: str = "storage/reports") -> str:
    case = db.get(Case, case_id)
    if not case:
        raise ValueError("Case not found")

    parties = db.scalars(select(Party).where(Party.case_id == case_id)).all()
    docs = db.scalars(select(Document).where(Document.case_id == case_id).order_by(Document.created_at.asc())).all()
    screenings = db.scalars(select(Screening).where(Screening.case_id == case_id).order_by(Screening.created_at.asc())).all()
    audits = db.scalars(select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.id.asc())).all()

    checklist = build_kyc_checklist(db, case_id)

    # Org / signature agence
    org_name = "Agence"
    try:
        org_name = case.created_by.organization.name
    except Exception:
        pass

    generated_at = datetime.now(timezone.utc)

    os.makedirs(output_dir, exist_ok=True)
    filename = f"ARGOS_AML_CASE_{case.reference}_CASEID_{case.id}.pdf".replace("/", "-")
    path = os.path.join(output_dir, filename)

    pdf = canvas.Canvas(path, pagesize=A4)
    y = 285 * mm

    # TITRE
    y = _draw_title(pdf, "DOSSIER DE CONFORMITE AML/CFT - ARGOS", y)
    y = _draw_kv(pdf, "Référence dossier", case.reference, y)
    y = _draw_kv(pdf, "Statut", str(case.status.value), y)
    y = _draw_kv(pdf, "Date génération (UTC)", generated_at.isoformat(), y)
    y = _draw_kv(pdf, "Agence (signature)", org_name, y)
    y -= 3 * mm

    # 1) TRANSACTION
    y = _draw_section(pdf, "1) Informations transactionnelles", y)
    y = _draw_kv(pdf, "Montant (FCFA)", str(case.amount_fcfa or ""), y)
    y = _draw_kv(pdf, "Mode de paiement", _safe(case.payment_mode), y)
    y = _draw_kv(pdf, "Origine des fonds", _safe(case.funds_origin), y)
    y = _draw_kv(pdf, "Pays de résidence", _safe(case.country_residence), y)
    y = _draw_kv(pdf, "Profession", _safe(case.profession), y)
    y = _new_page_if_needed(pdf, y)
    y -= 2 * mm

    # 2) PARTIES
    y = _draw_section(pdf, "2) Parties (Acheteur / Vendeur)", y)
    if not parties:
        y = _draw_kv(pdf, "Info", "Aucune partie enregistrée", y)
    else:
        for p in parties:
            y = _new_page_if_needed(pdf, y)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(20 * mm, y, f"- {p.party_type.value}: {p.last_name} {p.first_name}")
            y -= 5 * mm
            y = _draw_kv(pdf, "Date naissance", str(p.birth_date or ""), y)
            y = _draw_kv(pdf, "Nationalité", _safe(p.nationality), y)
            y = _draw_kv(pdf, "Adresse", _safe(p.address), y)
            y = _draw_kv(pdf, "Email", _safe(p.email), y)
            y = _draw_kv(pdf, "Téléphone", _safe(p.phone), y)
            y = _draw_kv(pdf, "Numéro ID", _safe(p.id_number), y)
            y -= 2 * mm
    y = _new_page_if_needed(pdf, y)

    # 3) KYC CHECKLIST + DOCUMENTS
    y = _draw_section(pdf, "3) KYC - Checklist & Documents reçus", y)
    y = _draw_kv(pdf, "KYC complet", "OUI" if checklist["is_complete"] else "NON", y)

    for item in checklist["parties"]:
        y = _new_page_if_needed(pdf, y)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(20 * mm, y, f"- {item['party_type']} : {item['name']} (party_id={item['party_id']})")
        y -= 5 * mm
        y = _draw_kv(pdf, "Docs présents", ", ".join(item["present_docs"]), y)
        y = _draw_kv(pdf, "Docs manquants", ", ".join(item["missing_docs"]), y)
        y -= 2 * mm

    y -= 2 * mm
    y = _draw_section(pdf, "Documents (liste)", y)
    if not docs:
        y = _draw_kv(pdf, "Info", "Aucun document uploadé", y)
    else:
        for d in docs:
            y = _new_page_if_needed(pdf, y)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(
                20 * mm,
                y,
                f"- {d.doc_type.value} | {d.filename} | party_id={d.party_id} | {d.created_at.isoformat() if d.created_at else ''}",
            )
            y -= 5 * mm
    y = _new_page_if_needed(pdf, y)

    # 4) SCREENING
    y = _draw_section(pdf, "4) Screening (Sanctions / PEP / Watchlists)", y)
    if not screenings:
        y = _draw_kv(pdf, "Info", "Aucun screening", y)
    else:
        for s in screenings:
            y = _new_page_if_needed(pdf, y)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(
                20 * mm,
                y,
                f"- {s.created_at.isoformat() if s.created_at else ''} | {s.provider} | query='{s.query}' | risk_flag={s.risk_flag}",
            )
            y -= 5 * mm

    # 5) SCORE
    y -= 2 * mm
    y = _draw_section(pdf, "5) Scoring automatique (V1)", y)
    y = _draw_kv(pdf, "Risk score", str(case.risk_score), y)

    details = {}
    if case.risk_details:
        try:
            details = json.loads(case.risk_details)
        except Exception:
            details = {"raw": case.risk_details}

    rules = details.get("rules", [])
    if rules:
        pdf.setFont("Helvetica", 9)
        for r in rules:
            y = _new_page_if_needed(pdf, y)
            pdf.drawString(20 * mm, y, f"- {r.get('rule')} : +{r.get('points')}")
            y -= 5 * mm
    else:
        y = _draw_kv(pdf, "Détails", "Aucun détail", y)

    # 6) DECISION CONFORMITE
    y -= 2 * mm
    y = _draw_section(pdf, "6) Décision conformité", y)
    y = _draw_kv(pdf, "Décision", str(case.compliance_decision.value) if case.compliance_decision else "", y)
    y = _draw_kv(pdf, "Commentaire", _safe(case.compliance_comment), y)
    y = _draw_kv(pdf, "Date validation", case.date_validation.isoformat() if case.date_validation else "", y)
    y = _draw_kv(pdf, "Validé par (user_id)", str(case.validated_by_user_id or ""), y)
    y = _new_page_if_needed(pdf, y)

    # 7) AUDIT LOG COMPLET
    y -= 2 * mm
    y = _draw_section(pdf, "7) Historique complet (Audit trail immuable)", y)

    if not audits:
        y = _draw_kv(pdf, "Info", "Aucun audit log", y)
    else:
        pdf.setFont("Helvetica", 8)
        for a in audits:
            y = _new_page_if_needed(pdf, y)
            pdf.drawString(
                20 * mm,
                y,
                f"- [{a.id}] {a.created_at.isoformat() if a.created_at else ''} | {a.action} | prev={a.prev_hash or ''} | hash={a.hash}",
            )
            y -= 4 * mm
            # details sur une ligne courte
            det = (a.details or "").replace("\n", " ")
            if len(det) > 120:
                det = det[:120] + "..."
            y = _new_page_if_needed(pdf, y)
            pdf.drawString(24 * mm, y, f"  details: {det}")
            y -= 5 * mm

    # Footer signature
    y = _new_page_if_needed(pdf, y)
    y -= 5 * mm
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20 * mm, y, f"Signature agence : {org_name}")
    y -= 6 * mm
    pdf.setFont("Helvetica", 9)
    pdf.drawString(20 * mm, y, "Document généré par ARGOS AML - Version Immobilier (Côte d’Ivoire)")

    pdf.save()
    return path