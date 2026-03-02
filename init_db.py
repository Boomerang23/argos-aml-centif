from app.db import engine, Base
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)
print("DB initialized")