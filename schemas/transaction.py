from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum as PyEnum

class TransactionType(PyEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class TransactionBase(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    recipient: Optional[str] = Field(None, max_length=255)
    amount: int = Field(description="Amount in cents/pence")
    type: TransactionType = Field(description="Type of the transaction")
    transaction_date: datetime = Field(description="Date of the transaction")
    meta_data: Optional[Dict] = None

class TransactionCreate(TransactionBase):
    category_id: Optional[int] = None
    budget_id: Optional[int] = None
    pot_id: Optional[int] = None
    sender: Optional[str] = None

class TransactionUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    recipient: Optional[str] = Field(None, max_length=255)
    sender: Optional[str] = Field(None, max_length=255)
    amount: Optional[int] = None
    type: Optional[TransactionType] = None
    transaction_date: Optional[datetime] = None
    category_id: Optional[int] = None
    budget_id: Optional[int] = None
    pot_id: Optional[int] = None
    meta_data: Optional[Dict] = None

class TransactionFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    type: Optional[TransactionType] = None
    category_id: Optional[int] = None
    budget_id: Optional[int] = None
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    recipient: Optional[str] = None
    sender: Optional[str] = None
    pot_id: Optional[int] = None
class Transaction(TransactionBase):
    id: int
    account_id: int
    category_id: Optional[int]
    sender: Optional[str] = None
    budget_id: Optional[int]
    created_at: datetime
    pot_id: Optional[int]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 


class TransactionSummaryRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


