# Pydantic schemas for User

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)
    is_activated: bool | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_activated: bool
    created_at: datetime
    updated_at: datetime