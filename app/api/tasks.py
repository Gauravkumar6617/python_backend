from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_current_user_id
from app.db.session import SessionLocal
from app.models.tasks import Task
from app.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Create Task
# -----------------------

@router.post("/create-task", response_model=TaskResponse)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # The logic above runs here
):
    task = Task(
        title=data.title,
        due_date=data.due_date,
        user_id=user_id # This 'user_id' is now the integer from the token
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
# -----------------------
# List Tasks
# -----------------------
@router.get("/get-task", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

# -----------------------
# Update Task
# -----------------------
@router.post("/update-task/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int, 
    data: TaskUpdate, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # Added protection
):
    # Important: Only let users update their OWN tasks
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    if data.title is not None:
        task.title = data.title
    if data.status is not None:
        task.status = data.status
    if data.due_date is not None: # Changed from due_date to match create_task
        task.due_date = data.due_date

    db.commit()
    db.refresh(task)
    return task
