from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import SessionLocal
from app.models.user import UserTable
from app.schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.get("/", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserTable).all()
    return users
