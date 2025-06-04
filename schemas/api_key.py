from pydantic import BaseModel
from typing import List
from datetime import datetime

class APIKeyCreate(BaseModel):
    name: str
    expires_in_days: int | None = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool

class GetAPIKeyResponse(BaseModel):
    data: List[APIKeyResponse]
    message: str

class APIKeyCreateResponse(BaseModel):
    data: dict[str, APIKeyResponse | str]
    message: str