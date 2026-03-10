from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import User, Organization, UserRole
from app.security import hash_password


def get_or_create_org(db: Session, name: str) -> Organization:
    org = db.query(Organization).filter(Organization.name == name).first()
    if org:
        return org
    org = Organization(name=name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def main():
    db = SessionLocal()
    try:
        # 1) Organisation
        org = get_or_create_org(db, "Argos Demo Agency")

        # 2) Admin
        email = "admin@argos.ci"
        password = "ChangeMe123!"

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("admin already exists")
            return

        user = User(
            org_id=org.id,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("admin created")
        print(f"org: {org.name} (id={org.id})")
        print(f"email: {email}")
        print(f"password: {password}")

    finally:
        db.close()


if __name__ == "__main__":
    main()