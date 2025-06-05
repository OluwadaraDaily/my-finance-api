from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models.budget import Budget
from schemas.budget import BudgetCreate, BudgetUpdate
from db.models.category import Category
from fastapi import HTTPException

class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    def create_budget(self, user_id: int, budget_data: BudgetCreate) -> Budget:
        """Create a new budget for a user"""
        # Verify category exists
        category = self.db.query(Category).filter(Category.id == budget_data.category_id, Category.user_id == user_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Verify start date is before end date
        if budget_data.start_date >= budget_data.end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        # Verify the budget does not already exist
        existing_budget = self.db.query(Budget).filter(Budget.name == budget_data.name, Budget.category_id == budget_data.category_id, Budget.user_id == user_id).first()
        if existing_budget:
            raise HTTPException(status_code=400, detail="Budget already exists")

        db_budget = Budget(
            user_id=user_id,
            category_id=budget_data.category_id,
            name=budget_data.name,
            description=budget_data.description,
            total_amount=budget_data.total_amount,
            spent_amount=0,
            remaining_amount=budget_data.total_amount,
            start_date=budget_data.start_date,
            end_date=budget_data.end_date,
            is_active=True
        )
        self.db.add(db_budget)
        self.db.commit()
        self.db.refresh(db_budget)
        return db_budget

    def get_budgets(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Budget]:
        """Get all budgets for a user"""
        return (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_budget_by_id(self, budget_id: int, user_id: int) -> Optional[Budget]:
        """Get a specific budget by ID"""
        return (
            self.db.query(Budget)
            .filter(
                Budget.id == budget_id,
                Budget.user_id == user_id,
                Budget.is_deleted == False
            )
            .first()
        )

    def update_budget(self, budget_id: int, user_id: int, budget_data: BudgetUpdate) -> Optional[Budget]:
        """Update a budget"""
        db_budget = self.get_budget_by_id(budget_id, user_id)
        if not db_budget:
            return None

        update_data = budget_data.model_dump(exclude_unset=True)
        
        # If total_amount is being updated and remaining_amount is not being updated, recalculate remaining_amount
        if "total_amount" in update_data and "remaining_amount" not in update_data:
            update_data["remaining_amount"] = update_data["total_amount"] - db_budget.spent_amount

        for field, value in update_data.items():
            setattr(db_budget, field, value)

        db_budget.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_budget)
        return db_budget

    def delete_budget(self, budget_id: int, user_id: int) -> bool:
        """Soft delete a budget"""
        db_budget = self.get_budget_by_id(budget_id, user_id)
        if not db_budget:
            return False

        db_budget.is_deleted = True
        db_budget.is_active = False
        db_budget.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def update_budget_spent_amount(self, budget_id: int, amount_change: int) -> Optional[Budget]:
        """Update the spent and remaining amounts of a budget"""
        db_budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not db_budget:
            return None

        db_budget.spent_amount += amount_change
        db_budget.remaining_amount = db_budget.total_amount - db_budget.spent_amount
        db_budget.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_budget)
        return db_budget 