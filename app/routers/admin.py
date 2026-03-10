from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..deps import get_db, get_current_user
from ..models import Organization, User, UserRole
from ..security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(user):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")


# -------- ORG --------
class OrgCreate(BaseModel):
    name: str


@router.post("/org")
def create_org(payload: OrgCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_admin(user)
    org = Organization(name=payload.name)
    db.add(org)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Organization already exists")
    db.refresh(org)
    return {"ok": True, "org_id": org.id, "name": org.name}


@router.get("/org/me")
def get_my_org(db: Session = Depends(get_db), user=Depends(get_current_user)):
    org = db.get(Organization, user.org_id)
    return {"org_id": org.id, "name": org.name}


# -------- USERS --------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


@router.post("/users")
def create_user(payload: UserCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_admin(user)

    u = User(
        org_id=user.org_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    db.refresh(u)
    return {"ok": True, "user_id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active}


@router.get("/users")
def list_users(db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_admin(user)
    users = db.scalars(select(User).where(User.org_id == user.org_id).order_by(User.id.asc())).all()
    return [
        {"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active, "created_at": u.created_at}
        for u in users
    ]


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_admin(user)

    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    if u.org_id != user.org_id:
        raise HTTPException(403, "Not allowed")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(u, k, v)

    db.commit()
    db.refresh(u)
    return {"ok": True, "id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active}