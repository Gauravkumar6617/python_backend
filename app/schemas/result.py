from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional

class ResultCreate(BaseModel):
    user_id: str
    topic: str
    total_questions: int
    attempted: int
    correct: int
    wrong: int
    score: float
    accuracy: float
    time_spent: int
    sectional_breakdown: Dict[str, int]

class ProgressResponse(BaseModel):
    avg_score: float
    avg_accuracy: float
    latest_sectional: Dict[str, int]
    weekly_trend: List[float]
    total_mocks: int

    class Config:
        from_attributes = True