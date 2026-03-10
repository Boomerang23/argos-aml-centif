import os
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def login_admin():
    r = client.post(
    "/auth/login",
    data={"username": "admin@argos.ci", "password": "ChangeMe123!"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow_smoke():
    headers = login_admin()

    # 1) create case
    r = client.post(
        "/cases",
        json={
            "reference": "TEST-IMMO-0001",
            "amount_fcfa": 60000000,
            "payment_mode": "CASH",
            "funds_origin": "inconnu",
            "country_residence": "CI",
            "profession": "Entrepreneur",
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    case = r.json()
    case_id = case["id"]

    # 2) add buyer party
    r = client.post(
        f"/cases/{case_id}/parties",
        json={
            "party_type": "BUYER",
            "last_name": "GBOCHO",
            "first_name": "Ange",
            "birth_date": "1997-01-01",
            "nationality": "CI",
            "address": "Abidjan",
            "email": "ange@example.com",
            "phone": "+2250102030405",
            "id_number": "CNI123456",
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text

    # 3) screening (mock si pas de clé)
    r = client.post(
        f"/screening/cases/{case_id}",
        json={"query": "Ange GBOCHO"},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    # 4) compliance decision
    r = client.post(
        f"/cases/{case_id}/compliance-decision",
        json={"decision": "VALIDATED", "comment": "OK"},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    # 5) dashboard
    r = client.get("/dashboard/summary", headers=headers)
    assert r.status_code == 200, r.text

    # 6) export PDF
    r = client.get(f"/reports/cases/{case_id}/pdf", headers=headers)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")