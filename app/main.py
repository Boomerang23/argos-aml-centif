from fastapi import FastAPI
from .routers import auth, cases, screening, reports, onboarding
from .db import Base, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Argos CENTIF Immobilier (CI)")
    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(cases.router)
    app.include_router(screening.router)
    app.include_router(reports.router)
    app.include_router(onboarding.router)
    return app

app = create_app()