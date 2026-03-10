import os
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..deps import get_db, get_current_user
from ..models import Case, Party, Document, DocumentType, UserRole
from ..services.onboarding import make_onboarding_token, verify_onboarding_token
from ..services.audit import log_audit
from ..services.kyc_checklist import build_kyc_checklist, recompute_case_status_with_kyc

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def _assert_case_access(user, case: Case):
    # multi-agence
    if case.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    # AGENT: seulement ses dossiers
    if user.role == UserRole.AGENT and case.created_by_user_id != user.id:
        raise HTTPException(403, "Not allowed")


@router.post("/cases/{case_id}/parties/{party_id}/link")
def create_onboarding_link(
    case_id: int,
    party_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    _assert_case_access(user, case)

    party = db.get(Party, party_id)
    if not party or party.case_id != case_id:
        raise HTTPException(404, "Party not found for this case")

    token = make_onboarding_token(case_id=case_id, party_id=party_id)
    url = f"http://127.0.0.1:8000/onboarding/upload?token={token}"  # MVP local

    log_audit(db, case_id, "ONBOARDING_LINK_CREATED", f"party_id={party_id}")
    db.commit()

    return {"url": url, "token": token}


@router.get("/status")
def onboarding_status(token: str, db: Session = Depends(get_db)):
    """
    Route publique (via token). Pas d'auth user ici.
    """
    try:
        payload = verify_onboarding_token(token)
    except ValueError:
        raise HTTPException(401, "Invalid or expired token")

    case_id = int(payload["case_id"])
    party_id = int(payload["party_id"])

    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    party = db.get(Party, party_id)
    if not party or party.case_id != case_id:
        raise HTTPException(404, "Party not found for this case")

    docs_for_party = db.scalars(
        select(Document).where(
            Document.case_id == case_id,
            Document.party_id == party_id
        )
    ).all()
    docs_types = {d.doc_type for d in docs_for_party}

    have_id = DocumentType.ID in docs_types
    have_addr = DocumentType.PROOF_ADDRESS in docs_types

    checklist = build_kyc_checklist(db, case_id)
    party_row = next((p for p in checklist["parties"] if p["party_id"] == party_id), None)
    missing_docs = party_row["missing_docs"] if party_row else ["ID", "PROOF_ADDRESS"]

    return {
        "case_id": case_id,
        "party_id": party_id,
        "have_id": have_id,
        "have_proof_address": have_addr,
        "required_missing": missing_docs,
        "case_status": case.status.value,
        "kyc_complete": checklist["is_complete"],
    }


@router.get("/cases/{case_id}/kyc-checklist")
def get_kyc_checklist(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    _assert_case_access(user, case)

    return build_kyc_checklist(db, case_id)


@router.get("/cases/{case_id}/documents")
def list_case_documents(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    _assert_case_access(user, case)

    docs = db.query(Document).filter(Document.case_id == case_id).order_by(Document.created_at.asc()).all()

    return [
        {
            "id": d.id,
            "party_id": d.party_id,
            "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type),
            "filename": d.filename,
            "storage_key": d.storage_key,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.get("/upload", response_class=HTMLResponse)
def upload_page(token: str):
    """
    Page publique (token).
    """
    token_json = json.dumps(token)

    html = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Onboarding KYC – Argos</title>
  <style>
    :root {
      --bg: #0b1220;
      --card: rgba(255,255,255,0.08);
      --card2: rgba(255,255,255,0.06);
      --text: rgba(255,255,255,0.92);
      --muted: rgba(255,255,255,0.70);
      --line: rgba(255,255,255,0.12);
      --shadow: 0 20px 60px rgba(0,0,0,0.45);
      --radius: 18px;
      --radius2: 14px;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      background: radial-gradient(1200px 600px at 15% 20%, rgba(124,58,237,0.25), transparent 55%),
                  radial-gradient(1000px 600px at 85% 10%, rgba(34,197,94,0.18), transparent 55%),
                  radial-gradient(1200px 800px at 50% 90%, rgba(59,130,246,0.18), transparent 60%),
                  var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .wrap {
      width: min(980px, 100%);
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
    }

    @media (max-width: 900px) {
      .wrap { grid-template-columns: 1fr; }
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .logo {
      width: 44px; height: 44px;
      border-radius: 14px;
      background: linear-gradient(135deg, rgba(124,58,237,1), rgba(59,130,246,1));
      box-shadow: 0 10px 30px rgba(124,58,237,0.35);
      display: grid; place-items: center;
      font-weight: 800;
    }
    .logo span { font-size: 16px; }
    .title { display: flex; flex-direction: column; line-height: 1.1; }
    .title h1 { margin: 0; font-size: 20px; letter-spacing: 0.2px; }
    .title p { margin: 4px 0 0; color: var(--muted); font-size: 13px; }

    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .card .inner { padding: 18px; }

    .hero {
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
      border-bottom: 1px solid var(--line);
      padding: 18px;
    }
    .hero h2 { margin: 0 0 8px; font-size: 18px; }
    .hero p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.45; }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    @media (max-width: 520px) { .grid { grid-template-columns: 1fr; } }

    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 8px; }
    .field {
      background: var(--card2);
      border: 1px solid var(--line);
      border-radius: var(--radius2);
      padding: 12px;
    }
    select, input[type="file"] {
      width: 100%;
      background: transparent;
      color: var(--text);
      border: none;
      outline: none;
      font-size: 14px;
    }
    option { color: #111827; }

    .btn {
      width: 100%;
      margin-top: 12px;
      background: linear-gradient(135deg, rgba(124,58,237,1), rgba(59,130,246,1));
      color: white;
      border: none;
      border-radius: 14px;
      padding: 12px 14px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(59,130,246,0.25);
      transition: transform 0.05s ease;
    }
    .btn:active { transform: translateY(1px); }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; }

    .hint { margin-top: 10px; font-size: 12px; color: var(--muted); line-height: 1.4; }

    .status {
      margin-top: 12px;
      border-radius: 14px;
      padding: 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.05);
      display: none;
    }
    .status.ok { border-color: rgba(34,197,94,0.4); background: rgba(34,197,94,0.10); }
    .status.warn { border-color: rgba(245,158,11,0.45); background: rgba(245,158,11,0.10); }
    .status.err { border-color: rgba(239,68,68,0.45); background: rgba(239,68,68,0.10); }
    .status .line1 { font-weight: 800; }
    .status .line2 { color: var(--muted); font-size: 12px; margin-top: 4px; }

    .steps { display: grid; gap: 10px; }
    .step {
      background: var(--card2);
      border: 1px solid var(--line);
      border-radius: var(--radius2);
      padding: 12px;
      display: flex;
      gap: 10px;
      align-items: flex-start;
    }
    .badge {
      width: 28px; height: 28px;
      border-radius: 10px;
      display: grid; place-items: center;
      font-weight: 800;
      background: rgba(124,58,237,0.25);
      border: 1px solid rgba(124,58,237,0.35);
      flex: 0 0 auto;
    }
    .step h3 { margin: 0; font-size: 13px; }
    .step p { margin: 4px 0 0; font-size: 12px; color: var(--muted); line-height: 1.4; }
  </style>
</head>

<body>
  <div class="wrap">
    <div class="card">
      <div class="hero">
        <div class="brand">
          <div class="logo"><span>AR</span></div>
          <div class="title">
            <h1>Argos – Onboarding KYC</h1>
            <p>Upload sécurisé pour compléter ton dossier immobilier (Côte d’Ivoire).</p>
          </div>
        </div>
      </div>

      <div class="inner">
        <div class="grid">
          <div>
            <label>Type de document</label>
            <div class="field">
              <select id="docType">
                <option value="ID">Pièce d’identité (CNI / Passeport)</option>
                <option value="PROOF_ADDRESS">Justificatif de domicile</option>
              </select>
            </div>
          </div>

          <div>
            <label>Fichier</label>
            <div class="field">
              <input id="file" type="file" accept=".png,.jpg,.jpeg,.pdf" />
            </div>
          </div>
        </div>

        <button class="btn" id="uploadBtn">Uploader le document</button>

        <div class="hint">
          Formats acceptés : PDF, JPG, PNG. Conseils : photo lisible, sans reflet, tout le document visible.
        </div>

        <div class="status" id="statusBox">
          <div class="line1" id="statusTitle"></div>
          <div class="line2" id="statusText"></div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="hero">
        <h2>Ce qu’on te demande</h2>
        <p>Tu complètes le dossier en 2 minutes. L’agence garde une preuve horodatée pour la conformité (CENTIF).</p>
      </div>
      <div class="inner">
        <div class="steps">
          <div class="step">
            <div class="badge">1</div>
            <div>
              <h3>Pièce d’identité</h3>
              <p>Carte nationale d’identité ou passeport.</p>
            </div>
          </div>
          <div class="step">
            <div class="badge">2</div>
            <div>
              <h3>Justificatif de domicile</h3>
              <p>Facture (eau/électricité) ou attestation.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

<script>
  const TOKEN = __TOKEN__;

  const btn = document.getElementById("uploadBtn");
  const fileInput = document.getElementById("file");
  const docType = document.getElementById("docType");

  const box = document.getElementById("statusBox");
  const title = document.getElementById("statusTitle");
  const text = document.getElementById("statusText");

  function showStatus(kind, t, msg) {
    box.style.display = "block";
    box.className = "status " + kind;
    title.textContent = t;
    text.textContent = msg;
  }

  async function refreshStatus() {
    const res = await fetch(`/onboarding/status?token=${encodeURIComponent(TOKEN)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return;

    const st = data.case_status || "ORANGE";
    if (st === "GREEN") showStatus("ok", "Dossier complet ✅", "Merci. L’agence a reçu les documents requis.");
    else if (st === "RED") showStatus("err", "Alerte 🚨", "Le dossier est en alerte. L’agence va traiter le cas.");
    else {
      const missing = (data.required_missing || []).join(", ");
      showStatus("warn", "Dossier incomplet (ORANGE)", missing ? `Documents manquants : ${missing}` : "Documents manquants.");
    }
  }

  btn.addEventListener("click", async () => {
    const f = fileInput.files[0];
    if (!f) {
      showStatus("warn", "Fichier manquant", "Choisis un fichier avant d'uploader.");
      return;
    }

    btn.disabled = true;
    showStatus("warn", "Upload en cours…", "Merci de patienter.");

    try {
      const form = new FormData();
      form.append("file", f);

      const url = `/onboarding/upload?token=${encodeURIComponent(TOKEN)}&doc_type=${encodeURIComponent(docType.value)}`;
      const res = await fetch(url, { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        showStatus("err", "Upload refusé", data?.detail || "Erreur lors de l’upload.");
        return;
      }

      fileInput.value = "";
      await refreshStatus();
    } catch {
      showStatus("err", "Erreur réseau", "Impossible de joindre le serveur. Réessaie.");
    } finally {
      btn.disabled = false;
    }
  });

  refreshStatus();
</script>

</body>
</html>
""".replace("__TOKEN__", token_json)

    return HTMLResponse(content=html, status_code=200)


@router.post("/upload")
def upload_document(
    token: str,
    doc_type: DocumentType,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Route publique (via token). Pas d'auth user ici.
    """
    try:
        payload = verify_onboarding_token(token)
    except ValueError:
        raise HTTPException(401, "Invalid or expired token")

    case_id = int(payload["case_id"])
    party_id = int(payload["party_id"])

    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    party = db.get(Party, party_id)
    if not party or party.case_id != case_id:
        raise HTTPException(404, "Party not found")

    os.makedirs("storage", exist_ok=True)
    safe_name = (file.filename or "upload").replace("/", "_").replace("\\", "_")
    storage_key = f"storage/case_{case_id}_party_{party_id}_{doc_type.value}_{safe_name}"

    with open(storage_key, "wb") as f:
        f.write(file.file.read())

    doc = Document(
        case_id=case_id,
        party_id=party_id,
        doc_type=doc_type,
        filename=file.filename or safe_name,
        storage_key=storage_key,
    )
    db.add(doc)

    # ✅ Recalcul KYC + statut auto
    checklist = recompute_case_status_with_kyc(db, case)

    # ✅ Audit + commit (sinon tu perds les logs)
    log_audit(db, case_id, "DOCUMENT_UPLOADED", f"party_id={party_id} doc_type={doc_type.value} file={safe_name}")
    log_audit(db, case_id, "KYC_CHECKLIST_UPDATED", f"is_complete={checklist['is_complete']} status={case.status.value}")

    db.commit()
    db.refresh(case)

    return {
        "ok": True,
        "storage_key": storage_key,
        "case_status": case.status.value,
        "kyc_complete": checklist["is_complete"],
    }