from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class AccountBase(BaseModel):
    balance: int = 0

class AccountCreate(AccountBase):
    user_id: int

class AccountUpdate(BaseModel):
    balance: Optional[int] = None

class Account(AccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 