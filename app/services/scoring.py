import json
from typing import Tuple, Dict, Any

from ..models import Case, CaseStatus


# ✅ Liste simple V1 (tu pourras la sortir en DB plus tard)
RISK_COUNTRIES = {
    # exemples
    "IR", "KP", "SY",
    # tu peux ajouter : "RU", "UA", etc selon ta politique interne
}

CASH_VALUES = {"CASH", "ESPECES", "ESPÈCES", "CASH_PAYMENT"}


def is_funds_unclear(funds_origin: str | None) -> bool:
    if not funds_origin:
        return True
    x = funds_origin.strip().lower()
    # règles simples V1 : si trop court ou mots vagues
    vague_keywords = ["n/a", "na", "inconnu", "inconnue", "aucune", "?", "non précisé", "non precise", "flou"]
    if len(x) < 6:
        return True
    return any(k in x for k in vague_keywords)


def compute_risk(case: Case, pep: bool) -> Tuple[int, Dict[str, Any]]:
    score = 0
    details: Dict[str, Any] = {"rules": [], "pep": pep}

    # 1) montant > 50M
    if case.amount_fcfa is not None and case.amount_fcfa > 50_000_000:
        score += 2
        details["rules"].append({"rule": "amount>50M", "points": 2})

    # 2) cash
    if case.payment_mode and case.payment_mode.strip().upper() in CASH_VALUES:
        score += 3
        details["rules"].append({"rule": "payment_cash", "points": 3})

    # 3) pays à risque
    if case.country_residence and case.country_residence.strip().upper() in RISK_COUNTRIES:
        score += 3
        details["rules"].append({"rule": "risk_country", "points": 3, "country": case.country_residence})

    # 4) origine floue
    if is_funds_unclear(case.funds_origin):
        score += 2
        details["rules"].append({"rule": "funds_unclear", "points": 2})

    # 5) PEP
    if pep:
        score += 5
        details["rules"].append({"rule": "pep", "points": 5})

    details["total"] = score
    return score, details


def status_from_score(score: int) -> CaseStatus:
    if score >= 7:
        return CaseStatus.RED
    if score >= 4:
        return CaseStatus.ORANGE
    return CaseStatus.GREEN


def apply_scoring(case: Case, pep: bool) -> None:
    """
    Met à jour le case.risk_score + risk_details + status.
    """
    score, details = compute_risk(case, pep=pep)
    case.risk_score = score
    case.risk_details = json.dumps(details, ensure_ascii=False)

    # statut = grille de décision
    case.status = status_from_score(score)