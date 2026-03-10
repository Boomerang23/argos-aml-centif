import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1) Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 2) Imports app
from app.db import Base
from app.deps import get_db
from app.main import app
from app.models import Organization, User, UserRole
from app.security import hash_password

# 3) DB SQLite de test (fichier)
TEST_DB_PATH = ROOT / "test.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Supprimer l'ancienne DB test si existe (évite les colonnes manquantes)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    # Créer tables
    Base.metadata.create_all(bind=engine)

    # Créer org + admin
    db = TestingSessionLocal()
    try:
        org = Organization(name="Test Org")
        db.add(org)
        db.commit()
        db.refresh(org)

        admin = User(
            org_id=org.id,
            email="admin@argos.ci",
            hashed_password=hash_password("ChangeMe123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()

    # Override dependency FastAPI
    app.dependency_overrides[get_db] = override_get_db

    yield

    # Cleanup
    app.dependency_overrides.clear()

    # ✅ Fermer toutes les connexions SQLite (Windows lock)
    engine.dispose()

    # ✅ Essayer de supprimer le fichier (avec retry simple)
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            # parfois Windows garde un lock quelques ms
            import time
            time.sleep(0.2)
            engine.dispose()
            TEST_DB_PATH.unlink()