import json
import httpx
from ..config import settings


async def opensanctions_search(q: str) -> dict:
    if not settings.OPENSANCTIONS_API_KEY:
        # Mode MVP: mock si pas de clé
        return {
            "query": q,
            "mock": True,
            "matches": [],
            "note": "No OPENSANCTIONS_API_KEY set"
        }

    url = f"{settings.OPENSANCTIONS_BASE_URL}/search/default"
    headers = {"Authorization": f"ApiKey {settings.OPENSANCTIONS_API_KEY}"}
    params = {"q": q}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()


def detect_risk(payload: dict) -> bool:
    matches = payload.get("results") or payload.get("matches") or []
    return len(matches) > 0


async def run_screening(query: str) -> dict:
    """
    Standardise la sortie pour le router.
    """
    result = await opensanctions_search(query)
    risk_flag = detect_risk(result)

    return {
        "provider": "OpenSanctions",
        "risk_flag": risk_flag,
        "result_json": json.dumps(result, ensure_ascii=False),
    }