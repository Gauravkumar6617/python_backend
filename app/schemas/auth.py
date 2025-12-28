from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Login(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True   # <-- important for Pydantic v2
    }

class LoginResponse(BaseModel):
    access_token: str
    user: UserOut
