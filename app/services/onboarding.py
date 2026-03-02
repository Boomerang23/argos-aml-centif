import hmac, hashlib, base64, json
from datetime import datetime, timedelta, timezone
from ..config import settings

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))

def make_onboarding_token(case_id: int, party_id: int) -> str:
    exp = (datetime.now(timezone.utc) + timedelta(hours=settings.ONBOARDING_LINK_TTL_HOURS)).isoformat()
    payload = {"case_id": case_id, "party_id": party_id, "exp": exp}
    payload_b = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(settings.ONBOARDING_LINK_SECRET.encode("utf-8"), payload_b, hashlib.sha256).digest()
    return f"{_b64url(payload_b)}.{_b64url(sig)}"

def verify_onboarding_token(token: str) -> dict:
    try:
        p1, p2 = token.split(".", 1)
        payload_b = _b64url_decode(p1)
        sig = _b64url_decode(p2)
        expected = hmac.new(settings.ONBOARDING_LINK_SECRET.encode("utf-8"), payload_b, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(payload_b.decode("utf-8"))
        exp = datetime.fromisoformat(payload["exp"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            raise ValueError("expired")
        return payload
    except Exception as e:
        raise ValueError("invalid token") from e