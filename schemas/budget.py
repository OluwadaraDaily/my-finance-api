from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class BudgetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    total_amount: int = Field(..., gt=0)
    category_id: int
    start_date: datetime
    end_date: datetime

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    total_amount: Optional[int] = Field(None, gt=0)
    category_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class BudgetInDB(BudgetBase):
    id: int
    user_id: int
    spent_amount: int
    remaining_amount: int
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Budget(BudgetInDB):
    pass 


class BudgetSummaryChart(BaseModel):
    label: str
    amount: int
    color: str

class BudgetSummary(BaseModel):
    total_spent_amount: int
    total_remaining_amount: int
    total_budget_amount: int
    budgets: List[BudgetSummaryChart]