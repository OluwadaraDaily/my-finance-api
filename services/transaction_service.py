from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, asc
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime, timezone

from db.models.transaction import Transaction
from schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilter, TransactionType, TransactionResponse
from db.models.user import User
from schemas.transaction import CategoryWithBudget, CategoryWithPot
from services.budget_service import BudgetService

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.budget_service = BudgetService(db)

    def _adjust_account_balance(self, transaction: Transaction) -> None:
        """Helper method to adjust account balance based on transaction type"""
        if transaction.type == TransactionType.CREDIT:
            transaction.account.balance += transaction.amount
        else:  # DEBIT
            transaction.account.balance -= transaction.amount

    def _revert_account_balance(self, transaction: Transaction) -> None:
        """Helper method to revert account balance changes"""
        if transaction.type == TransactionType.CREDIT:
            transaction.account.balance -= transaction.amount
        else:  # DEBIT
            transaction.account.balance += transaction.amount

    def _update_budget_for_transaction(self, transaction: Transaction, is_new: bool = True, old_amount: Optional[int] = None) -> None:
        """Helper method to update budget amounts when a transaction changes"""
        if not transaction.budget_id:
            return

        is_debit = transaction.type == TransactionType.DEBIT
        
        if is_new:
            # New transaction - simply update with the full amount
            self.budget_service.update_budget_amounts(
                budget_id=transaction.budget_id,
                amount_change=transaction.amount,
                is_debit=is_debit,
                user_id=transaction.user_id
            )
        else:
            # Updated transaction - calculate the difference
            amount_change = transaction.amount - old_amount if old_amount is not None else transaction.amount
            if amount_change != 0:
                self.budget_service.update_budget_amounts(
                    budget_id=transaction.budget_id,
                    amount_change=amount_change,
                    is_debit=is_debit,
                    user_id=transaction.user_id
                )

    def create_transaction(self, transaction_data: TransactionCreate, user: User) -> Transaction:
        """Create a new transaction"""
        # Check for duplicate transaction
        if self.db.query(Transaction).filter(
            Transaction.account_id == user.account.id,
            Transaction.description == transaction_data.description,
            Transaction.recipient == transaction_data.recipient,
            Transaction.amount == transaction_data.amount,
            Transaction.transaction_date == transaction_data.transaction_date,
        ).first():
            raise HTTPException(status_code=400, detail="Transaction already exists")
        
        db_transaction = Transaction(
            account_id=user.account.id,
            category_id=transaction_data.category_id,
            budget_id=transaction_data.budget_id,
            description=transaction_data.description,
            recipient=transaction_data.recipient if transaction_data.type == TransactionType.DEBIT else user.username,
            sender=transaction_data.sender if transaction_data.type == TransactionType.CREDIT else user.username,
            amount=transaction_data.amount,
            type=transaction_data.type,
            transaction_date=transaction_data.transaction_date,
            meta_data=transaction_data.meta_data,
            user_id=user.id,
            pot_id=transaction_data.pot_id
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        
        # Update account balance
        self._adjust_account_balance(db_transaction)
        
        # Update budget amounts if this transaction is associated with a budget
        self._update_budget_for_transaction(db_transaction)
        
        # Commit all changes
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def get_transactions(
        self,
        account_id: int,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "transaction_date",
        sort_order: str = "desc",
        filters: Optional[TransactionFilter] = None
    ) -> List[Transaction]:
        """Get all transactions with filtering and sorting"""
        # Start with a query that eagerly loads budget and pot using selectinload
        query = (
            self.db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .options(
                selectinload(Transaction.budget),
                selectinload(Transaction.pot)
            )
        )

        # Apply filters if provided
        if filters:
            if filters.start_date:
                query = query.filter(Transaction.transaction_date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Transaction.transaction_date <= filters.end_date)
            if filters.type:
                query = query.filter(Transaction.type == filters.type)
            if filters.category_id:
                query = query.filter(Transaction.category_id == filters.category_id)
            if filters.budget_id:
                query = query.filter(Transaction.budget_id == filters.budget_id)
            if filters.min_amount:
                query = query.filter(Transaction.amount >= filters.min_amount)
            if filters.max_amount:
                query = query.filter(Transaction.amount <= filters.max_amount)
            if filters.recipient:
                query = query.filter(Transaction.recipient.ilike(f"%{filters.recipient}%"))
            if filters.sender:
                query = query.filter(Transaction.sender.ilike(f"%{filters.sender}%"))
            if filters.pot_id:
                query = query.filter(Transaction.pot_id == filters.pot_id)

        # Apply sorting
        sort_column = getattr(Transaction, sort_by, Transaction.transaction_date)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return query.offset(skip).limit(limit).all()

    def get_transaction_by_id(self, transaction_id: int, account_id: int) -> Optional[Transaction]:
        """Get a specific transaction by ID"""
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.account_id == account_id
        ).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction

    def update_transaction(
        self,
        transaction_id: int,
        account_id: int,
        transaction_data: TransactionUpdate
    ) -> Transaction:
        """Update a transaction's details"""
        transaction = self.get_transaction_by_id(transaction_id, account_id)
        
        # Store old values for balance adjustment
        old_amount = transaction.amount
        old_type = transaction.type
        old_budget_id = transaction.budget_id
        
        # Update the transaction with the new data
        update_data = transaction_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        # If amount or type changed, adjust the balance
        if transaction_data.amount is not None or transaction_data.type is not None:
            # First revert the old transaction's effect on balance
            if old_type == TransactionType.CREDIT:
                transaction.account.balance -= old_amount
            else:
                transaction.account.balance += old_amount
            
            # Then apply the new transaction's effect
            self._adjust_account_balance(transaction)

        # Handle budget updates
        if old_budget_id != transaction.budget_id:
            # If budget changed, revert changes from old budget and update new budget
            if old_budget_id:
                # Revert changes from old budget
                self.budget_service.update_budget_amounts(
                    budget_id=old_budget_id,
                    amount_change=old_amount,
                    is_debit=old_type == TransactionType.DEBIT,
                    user_id=transaction.user_id
                )
            
            # Update new budget if it exists
            if transaction.budget_id:
                self._update_budget_for_transaction(transaction)
        else:
            # Same budget, but amount might have changed
            self._update_budget_for_transaction(transaction, is_new=False, old_amount=old_amount)
        
        transaction.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete_transaction(self, transaction_id: int, account_id: int) -> bool:
        """Delete a transaction"""
        transaction = self.get_transaction_by_id(transaction_id, account_id)
        
        # Revert the account balance changes
        self._revert_account_balance(transaction)
        
        # If transaction was associated with a budget, update the budget amounts
        if transaction.budget_id:
            # We need to revert the transaction's effect on the budget
            # For a deletion, this means applying the opposite of what the transaction did
            self.budget_service.update_budget_amounts(
                budget_id=transaction.budget_id,
                amount_change=transaction.amount,
                is_debit=transaction.type != TransactionType.DEBIT,
                user_id=transaction.user_id
            )
        
        self.db.delete(transaction)
        self.db.commit()
        return True

    def get_transaction_summary(
        self,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get a summary of transactions for an account"""
        query = self.db.query(Transaction).filter(Transaction.account_id == account_id)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        transactions = query.all()
        
        total_income = sum(t.amount for t in transactions if t.type == TransactionType.CREDIT)
        total_expense = sum(t.amount for t in transactions if t.type == TransactionType.DEBIT)
        print("total_expense =>", total_expense)
        
        return {
            "total_transactions": len(transactions),
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense
        } 
    
    def get_transactions_by_budget(self, budget_id: int, account_id: int) -> List[Transaction]:
        """Get all transactions by budget"""
        return self.db.query(Transaction).filter(Transaction.budget_id == budget_id, Transaction.account_id == account_id).all()
    
    def get_transactions_by_pot(self, pot_id: int, account_id: int) -> List[Transaction]:
        """Get all transactions by pot"""
        return self.db.query(Transaction).filter(Transaction.pot_id == pot_id, Transaction.account_id == account_id).all()
    
    def get_transactions_by_category(self, category_id: int, account_id: int) -> List[Transaction]:
        """Get all transactions by category"""
        return self.db.query(Transaction).filter(Transaction.category_id == category_id, Transaction.account_id == account_id).all()