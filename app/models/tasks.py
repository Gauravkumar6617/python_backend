from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean, ForeignKey
from datetime import datetime
from app.db.db import Base
from sqlalchemy.orm import relationship

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    status = Column(SmallInteger, default=0)
    due_date = Column(DateTime, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Change "User" to "UserTable" to match the class name in your user model
    user = relationship("UserTable", back_populates="tasks")