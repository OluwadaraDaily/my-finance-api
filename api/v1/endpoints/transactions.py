from fastapi import APIRouter, Depends, Query, status, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.deps import get_current_user
from db.models.user import User
from db.session import get_db
from services.transaction_service import TransactionService
from schemas.transaction import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    TransactionFilter
)
from schemas.common import ResponseModel, ListResponseModel

router = APIRouter()

@router.post("/", response_model=ResponseModel[Transaction], status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    transaction_service = TransactionService(db)
    transaction = transaction_service.create_transaction(transaction_data, current_user)
    return ResponseModel[Transaction](
        data=transaction,
        message="Transaction created successfully"
    )

@router.get("/", response_model=ListResponseModel[Transaction])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    sort_by: str = Query("transaction_date", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    budget_id: Optional[int] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    recipient: Optional[str] = None,
    sender: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions with filtering and sorting"""
    transaction_service = TransactionService(db)
    
    filters = TransactionFilter(
        start_date=start_date,
        end_date=end_date,
        type=type,
        category_id=category_id,
        budget_id=budget_id,
        min_amount=min_amount,
        max_amount=max_amount,
        recipient=recipient,
        sender=sender
    )
    
    transactions = transaction_service.get_transactions(
        account_id=current_user.account.id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        filters=filters
    )
    
    return ListResponseModel[Transaction](
        data=transactions,
        message="Transactions fetched successfully"
    )

@router.get("/summary", response_model=ResponseModel[dict])
async def get_transaction_summary(
    start_date: Optional[str] = Query(None, description="Start date in format YYYY-MM-DDThh:mm:ssZ"),
    end_date: Optional[str] = Query(None, description="End date in format YYYY-MM-DDThh:mm:ssZ"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a summary of transactions for an account"""
    transaction_service = TransactionService(db)
    
    # Convert string dates to datetime if provided
    try:
        start_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) if start_date else None
        end_datetime = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) if end_date else None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Please use format YYYY-MM-DDThh:mm:ssZ. Error: {str(e)}"
        )
    
    summary = transaction_service.get_transaction_summary(
        account_id=current_user.account.id,
        start_date=start_datetime,
        end_date=end_datetime
    )
    return ResponseModel[dict](
        data=summary,
        message="Transaction summary fetched successfully"
    )

@router.get("/{transaction_id}", response_model=ResponseModel[Transaction])
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction by ID"""
    transaction_service = TransactionService(db)
    transaction = transaction_service.get_transaction_by_id(transaction_id=transaction_id, account_id=current_user.account.id)
    return ResponseModel[Transaction](
        data=transaction,
        message="Transaction fetched successfully"
    )

@router.get("/budgets/{budget_id}", response_model=ListResponseModel[Transaction])
async def get_transactions_by_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions by budget"""
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions_by_budget(
        budget_id=budget_id,
        account_id=current_user.account.id
    )
    return ListResponseModel[Transaction](
        data=transactions,
        message="Transactions fetched successfully"
    )

@router.get("/pots/{pot_id}", response_model=ListResponseModel[Transaction])
async def get_transactions_by_pot(
    pot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions by pot"""
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions_by_pot(
        pot_id=pot_id,
        account_id=current_user.account.id
    )
    return ListResponseModel[Transaction](
        data=transactions,
        message="Transactions fetched successfully"
    )

@router.get("/categories/{category_id}", response_model=ListResponseModel[Transaction])
async def get_transactions_by_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions by category"""
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions_by_category(
        category_id=category_id,
        account_id=current_user.account.id
    )
    return ListResponseModel[Transaction](
        data=transactions,
        message="Transactions fetched successfully"
    )

@router.put("/{transaction_id}", response_model=ResponseModel[Transaction])
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a transaction's details"""
    transaction_service = TransactionService(db)
    transaction = transaction_service.update_transaction(
        transaction_id=transaction_id,
        account_id=current_user.account.id,
        transaction_data=transaction_data
    )
    return ResponseModel[Transaction](
        data=transaction,
        message="Transaction updated successfully"
    )

@router.delete("/{transaction_id}", response_model=ResponseModel[bool])
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    transaction_service = TransactionService(db)
    result = transaction_service.delete_transaction(
        transaction_id=transaction_id, 
        account_id=current_user.account.id
    )
    return ResponseModel[bool](
        data=result,
        message="Transaction deleted successfully"
    ) 