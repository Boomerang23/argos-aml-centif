from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .immutability import setup_immutability_listeners
from .routers import auth, cases, screening, reports, onboarding, admin, dashboard, health


def create_app() -> FastAPI:
    # ✅ active l’immutabilité avant tout
    setup_immutability_listeners()

    app = FastAPI(title="Argos CENTIF Immobilier (CI)")

    # ✅ CORS (configurable via CORS_ORIGINS; default = local dev)
    allow_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ dev only: create_all (plus tard Alembic en prod)
    Base.metadata.create_all(bind=engine)

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(cases.router)
    app.include_router(screening.router)
    app.include_router(reports.router)
    app.include_router(onboarding.router)
    app.include_router(admin.router)
    app.include_router(dashboard.router)

    return app


app = create_app()