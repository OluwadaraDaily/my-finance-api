from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class PotBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    target_amount: int = Field(..., gt=0)
    color: Optional[str] = Field("#000000", max_length=255)

class PotCreate(PotBase):
    pass

class PotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    target_amount: Optional[int] = Field(None, gt=0)
    color: Optional[str] = Field(None, max_length=255)
    saved_amount: Optional[int] = Field(None, ge=0)

class UpdateSavedAmount(BaseModel):
    amount: int = Field(...)

class Pot(PotBase):
    id: int
    saved_amount: int
    
    model_config = ConfigDict(from_attributes=True)

class PotSummary(BaseModel):
    total_saved_amount: int
    total_target_amount: int
    average_progress: float
    pots: List[Pot]