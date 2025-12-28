from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.db import Base
from sqlalchemy.orm import relationship
class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    # Optional but professional
    full_name = Column(String, nullable=True)           # User's full name
    created_at = Column(DateTime, default=datetime.utcnow)  # Record creation time
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Record update time
    tasks = relationship("Task", back_populates="user")
