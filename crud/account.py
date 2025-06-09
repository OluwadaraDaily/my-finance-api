from typing import Optional
from sqlalchemy.orm import Session
from db.models.account import Account
from schemas.account import AccountUpdate

class AccountCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get(self, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        return self.db.query(Account).filter(Account.id == account_id).first()

    def get_by_user_id(self, user_id: int) -> Optional[Account]:
        """Get user's account"""
        return self.db.query(Account).filter(Account.user_id == user_id).first()

    def create(self, user_id: int, initial_balance: int = 0) -> Account:
        """Create new account for user"""
        # Check if user already has an account
        existing_account = self.get_by_user_id(user_id)
        if existing_account:
            return existing_account
            
        db_account = Account(
            user_id=user_id,
            balance=initial_balance
        )
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        return db_account

    def update(self, account_id: int, account: AccountUpdate) -> Optional[Account]:
        """Update account"""
        db_account = self.get(account_id)
        if not db_account:
            return None
        
        update_data = account.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_account, field, value)
        
        self.db.commit()
        self.db.refresh(db_account)
        return db_account

    def delete(self, account_id: int) -> bool:
        """Delete account"""
        db_account = self.get(account_id)
        if not db_account:
            return False
        
        self.db.delete(db_account)
        self.db.commit()
        return True 