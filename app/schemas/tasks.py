from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    title:str
    due_date:Optional[datetime]=None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title:Optional[str]=None
    status:Optional[int]=None
    due_date:Optional[datetime]=None


class TaskResponse(TaskBase):
    id:int
    status:int
    reminder_sent:bool
    created_at:datetime
    updated_at:datetime

    class config:
        from_attributes = True


