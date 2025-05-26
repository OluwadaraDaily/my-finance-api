# Pydantic schemas for User

from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    is_activated: bool
    created_at: datetime
    updated_at: datetime