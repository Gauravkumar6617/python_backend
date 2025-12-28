from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
# Import the models and schemas modules
from app import models, schemas
from app.db.session import SessionLocal

# Remove this line to avoid confusion:
# from app.schemas.result import ResultCreate, ProgressResponse 

router = APIRouter()
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/save-result")
def save_result(result: schemas.ResultCreate, db: Session = Depends(get_db)):
    """
    Saves a completed exam result to the PostgreSQL database.
    """
    try:
        db_result = models.ExamResult(
            user_id=result.user_id,
            topic=result.topic,
            total_questions=result.total_questions,
            attempted=result.attempted,
            correct=result.correct,
            wrong=result.wrong,
            score=result.score,
            accuracy=result.accuracy,
            time_spent=result.time_spent,
            sectional_breakdown=result.sectional_breakdown
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return {"status": "success", "result_id": db_result.id}
    except Exception as e:
        db.rollback()
        # Log the error for debugging
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/progress/{user_id}", response_model=schemas.ProgressResponse)
def get_progress(user_id: str, db: Session = Depends(get_db)):
    """
    Calculates analytics for the Progress Tab.
    """
    results = db.query(models.ExamResult).filter(
        models.ExamResult.user_id == user_id
    ).order_by(models.ExamResult.created_at.desc()).all()

    if not results:
        raise HTTPException(status_code=404, detail="No exam history found.")

    # Calculations
    total_exams = len(results)
    avg_score = sum(r.score for r in results) / total_exams
    avg_accuracy = sum(r.accuracy for r in results) / total_exams
    latest_sectional = results[0].sectional_breakdown
    
    # Chronological trend for the graph
    trend_data = [r.score for r in results[:7]][::-1]

    return {
        "avg_score": round(avg_score, 2),
        "avg_accuracy": round(avg_accuracy, 2),
        "latest_sectional": latest_sectional,
        "weekly_trend": trend_data,
        "total_mocks": total_exams
    }

@router.get("/dashboard-stats/{user_id}")
def get_dashboard_stats(user_id: str, db: Session = Depends(get_db)):
    results = db.query(models.ExamResult).filter(models.ExamResult.user_id == user_id).all()
    
    if not results:
        return {"msg": "No data found"}

    # Calculate Aggregates
    total_mocks = len(results)
    avg_score = sum(r.score for r in results) / total_mocks
    avg_accuracy = sum(r.accuracy for r in results) / total_mocks
    
    # Prepare data for a Line Chart (Last 10 mocks)
    chart_data = [
        {"date": r.created_at.strftime("%d %b"), "score": r.score} 
        for r in results[-10:]
    ]

    return {
        "total_mocks": total_mocks,
        "avg_score": round(avg_score, 2),
        "avg_accuracy": round(avg_accuracy, 2),
        "chart_data": chart_data
    }