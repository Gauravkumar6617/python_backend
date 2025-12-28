from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) 
    topic = Column(String)
    total_questions = Column(Integer)
    attempted = Column(Integer)
    correct = Column(Integer)
    wrong = Column(Integer)
    score = Column(Float)
    accuracy = Column(Float)
    time_spent = Column(Integer) 
    sectional_breakdown = Column(JSON) 
    created_at = Column(DateTime, default=datetime.utcnow)