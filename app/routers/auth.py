from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import settings
from ..deps import get_db, get_current_user
from ..models import User
from ..rate_limit import check_login_rate_limit
from ..schemas import UserMeOut
from ..security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie name for JWT (HTTP-only, not readable by JS)
ACCESS_TOKEN_COOKIE = "access_token"


def _get_client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


@router.get("/me", response_model=UserMeOut)
def get_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user (email, role, org_id)."""
    return UserMeOut(email=user.email, role=user.role, org_id=user.org_id)


def _cookie_secure() -> bool:
    """Use Secure flag only in production (HTTPS)."""
    env = (settings.ENVIRONMENT or "").strip().lower()
    return env in ("production", "prod")


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    check_login_rate_limit(_get_client_ip(request))
    user = db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Bad credentials")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")

    token = create_access_token(sub=user.email)
    max_age_seconds = settings.ACCESS_TOKEN_MINUTES * 60

    response = JSONResponse(content={"ok": True})
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout():
    """Clear the auth cookie. Frontend should call this then redirect to login."""
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")
    return response