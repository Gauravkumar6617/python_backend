from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import Login
from app.services.AuthService import AuthService
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(data: Login, db: Session = Depends(get_db)):
    return AuthService.login(data, db)
