from app.db import SessionLocal
from app.models import User
from app.security import hash_password

db = SessionLocal()
u = User(email="admin@argos.ci", hashed_password=hash_password("ChangeMe123!"))
db.add(u)
db.commit()
print("admin created")