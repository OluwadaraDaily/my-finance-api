from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from db.models.budget import Budget
from schemas.budget import BudgetCreate, BudgetUpdate
from fastapi import HTTPException

class BudgetCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, budget_data: BudgetCreate) -> Budget:
        """Create a new budget in the database"""
        db_budget = Budget(
            user_id=user_id,
            category_id=budget_data.category_id,
            name=budget_data.name,
            description=budget_data.description,
            total_amount=budget_data.total_amount,
            spent_amount=0,
            remaining_amount=budget_data.total_amount,
            start_date=budget_data.start_date,
            color=budget_data.color,
            end_date=budget_data.end_date,
            is_active=True
        )
        self.db.add(db_budget)
        self.db.commit()
        self.db.refresh(db_budget)
        return db_budget

    def get_multi(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Budget]:
        """Get multiple budgets with their transactions"""
        return (
            self.db.query(Budget)
            .options(joinedload(Budget.transactions))
            .filter(Budget.user_id == user_id, Budget.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, budget_id: int, user_id: int) -> Optional[Budget]:
        """Get a budget by ID with its transactions"""
        return (
            self.db.query(Budget)
            .options(joinedload(Budget.transactions))
            .filter(
                Budget.id == budget_id,
                Budget.user_id == user_id,
                Budget.is_deleted == False
            )
            .first()
        )

    def update(self, db_budget: Budget, update_data: dict) -> Budget:
        """Update a budget with given data"""
        for field, value in update_data.items():
            setattr(db_budget, field, value)
        
        db_budget.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_budget)
        return db_budget

    def soft_delete(self, db_budget: Budget) -> bool:
        """Soft delete a budget"""
        db_budget.is_deleted = True
        db_budget.is_active = False
        db_budget.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def update_spent_amount(self, budget_id: int, amount_change: int) -> Optional[Budget]:
        """Update the spent and remaining amounts of a budget"""
        db_budget = (
            self.db.query(Budget)
            .options(joinedload(Budget.transactions))
            .filter(Budget.id == budget_id)
            .first()
        )
        if not db_budget:
            return None

        db_budget.spent_amount += amount_change
        db_budget.remaining_amount = db_budget.total_amount - db_budget.spent_amount
        db_budget.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_budget)
        return db_budget 