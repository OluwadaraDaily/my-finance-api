from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from crud.account import AccountCRUD
from schemas.account import AccountUpdate, Account as AccountSchema, AccountCreate

class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.crud = AccountCRUD(db)

    def create_account(self, account_data: AccountCreate) -> AccountSchema:
        """Create a new account with specified user_id and initial balance"""
        # Check if user already has an account
        existing_account = self.crud.get_by_user_id(account_data.user_id)
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an account"
            )
        
        # Create a new account with the specified balance
        account = self.crud.create(account_data.user_id, initial_balance=account_data.balance)
        return AccountSchema.model_validate(account)

    def get_or_create_account(self, user_id: int) -> AccountSchema:
        """Get user's account or create one if it doesn't exist"""
        account = self.crud.get_by_user_id(user_id)
        if account:
            return AccountSchema.model_validate(account)
        
        # Create a new account with 0 balance
        account = self.crud.create(user_id, initial_balance=0)
        return AccountSchema.model_validate(account)

    def get_account(self, account_id: int) -> AccountSchema:
        """Get account by ID"""
        db_account = self.crud.get(account_id)
        if not db_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return AccountSchema.model_validate(db_account)

    def update_account(self, account_id: int, account: AccountUpdate) -> AccountSchema:
        """Update account"""
        db_account = self.crud.update(account_id, account)
        if not db_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return AccountSchema.model_validate(db_account)

    def delete_account(self, account_id: int) -> bool:
        """Delete account"""
        if not self.crud.delete(account_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return True 