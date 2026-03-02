import io, json, hashlib
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def build_case_pdf(case_dict: dict) -> tuple[bytes, str]:
    """
    Returns: (pdf_bytes, sha256_hex)
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    now = datetime.now(timezone.utc).isoformat()

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, h - 50, "Dossier de conformité - CENTIF (Immobilier)")

    c.setFont("Helvetica", 10)
    y = h - 80
    for line in [
        f"Référence: {case_dict['reference']}",
        f"Statut: {case_dict['status']}",
        f"Horodatage (UTC): {now}",
        f"Montant (FCFA): {case_dict.get('amount_fcfa')}",
        f"Mode de paiement: {case_dict.get('payment_mode')}",
        f"Pays de résidence: {case_dict.get('country_residence')}",
        f"Origine des fonds: {case_dict.get('funds_origin')}",
    ]:
        c.drawString(40, y, str(line))
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Parties")
    y -= 18
    c.setFont("Helvetica", 10)
    for p in case_dict.get("parties", []):
        c.drawString(40, y, f"- {p['party_type']}: {p['full_name']} | Nationalité: {p.get('nationality')} | ID: {p.get('id_number')}")
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Screenings")
    y -= 18
    c.setFont("Helvetica", 10)
    for s in case_dict.get("screenings", []):
        c.drawString(40, y, f"- Provider: {s['provider']} | Query: {s['query']} | Flag: {s['risk_flag']} | Date: {s['created_at']}")
        y -= 14

    c.showPage()
    c.save()

    pdf = buf.getvalue()
    sha = hashlib.sha256(pdf).hexdigest()
    return pdf, sha