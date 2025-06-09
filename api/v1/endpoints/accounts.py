from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from core.deps import get_current_user, get_api_key_user
from db.models.user import User
from db.session import get_db
from sqlalchemy.orm import Session
from services.account_service import AccountService
from schemas.account import Account, AccountCreate, AccountUpdate
from schemas.common import ResponseModel, ListResponseModel

router = APIRouter()

@router.post("/", response_model=ResponseModel[Account], status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new account"""
    account_service = AccountService(db)
    account = account_service.create_account(account_data)
    return ResponseModel[Account](
        data=account,
        message="Account created successfully"
    )

@router.get("/me", response_model=ResponseModel[Account])
async def get_my_account(
    current_user: User = Depends(get_current_user) or Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """Get or create the user's account"""
    account_service = AccountService(db)
    account = account_service.get_or_create_account(current_user.id)
    return ResponseModel[Account](
        data=account,
        message="Account fetched successfully"
    )

@router.get("/{account_id}", response_model=ResponseModel[Account])
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific account by ID"""
    account_service = AccountService(db)
    account = account_service.get_account(account_id)
    # Verify account belongs to current user
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account"
        )
    return ResponseModel[Account](
        data=account,
        message="Account fetched successfully"
    )

@router.put("/me", response_model=ResponseModel[Account])
async def update_my_account(
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the user's account"""
    account_service = AccountService(db)
    # Get the user's account
    account = account_service.get_or_create_account(current_user.id)
    # Update it
    updated_account = account_service.update_account(account.id, account_data)
    return ResponseModel[Account](
        data=updated_account,
        message="Account updated successfully"
    )

@router.delete("/me", response_model=ResponseModel[bool])
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete the user's account"""
    account_service = AccountService(db)
    # Get the user's account
    account = account_service.get_or_create_account(current_user.id)
    # Delete it
    result = account_service.delete_account(account.id)
    return ResponseModel[bool](
        data=result,
        message="Account deleted successfully"
    ) 