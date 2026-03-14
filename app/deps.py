from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import SessionLocal
from .security import decode_token
from .models import User

# Cookie name must match auth router (HTTP-only cookie for browser; Bearer for Swagger)
ACCESS_TOKEN_COOKIE = "access_token"
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_token(request: Request, bearer: str | None = Depends(oauth2)) -> str | None:
    """Token from cookie (browser) or Authorization header (e.g. Swagger)."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if token:
        return token
    if bearer:
        return bearer
    return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str | None = Depends(get_token), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")
    return user