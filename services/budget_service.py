from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from db.models.budget import Budget
from schemas.budget import BudgetCreate, BudgetUpdate, BudgetSummary, BudgetSummaryChart
from crud.budget import BudgetCRUD
from fastapi import HTTPException

class BudgetService:
    def __init__(self, db: Session):
        self.db = db
        self.crud = BudgetCRUD(db)

    def create_budget(self, user_id: int, budget_data: BudgetCreate) -> Budget:
        """Create a new budget for a user with validation"""

        print("budget_data =>", budget_data)
        
        # Verify start date is before end date
        if budget_data.start_date >= budget_data.end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        # Verify the budget does not already exist
        existing_budget = self.crud.get_multi(
            user_id=user_id,
            skip=0,
            limit=1
        )
        if existing_budget and any(b.name == budget_data.name and b.category_id == budget_data.category_id for b in existing_budget):
            raise HTTPException(status_code=400, detail="Budget already exists")

        return self.crud.create(user_id=user_id, budget_data=budget_data)

    def get_budgets(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Budget]:
        """Get all budgets for a user with their transactions"""
        return self.crud.get_multi(
            user_id=user_id, 
            skip=skip, 
            limit=limit
        )

    def get_budget_by_id(self, budget_id: int, user_id: int) -> Optional[Budget]:
        """Get a specific budget by ID with its transactions"""
        return self.crud.get_by_id(
            budget_id=budget_id, 
            user_id=user_id
        )

    def update_budget(self, budget_id: int, user_id: int, budget_data: BudgetUpdate) -> Optional[Budget]:
        """Update a budget with business logic"""
        db_budget = self.crud.get_by_id(budget_id=budget_id, user_id=user_id)
        if not db_budget:
            return None

        update_data = budget_data.model_dump(exclude_unset=True)
        
        # If total_amount is being updated and remaining_amount is not being updated, recalculate remaining_amount
        if "total_amount" in update_data and "remaining_amount" not in update_data:
            update_data["remaining_amount"] = update_data["total_amount"] - db_budget.spent_amount

        return self.crud.update(db_budget=db_budget, update_data=update_data)

    def delete_budget(self, budget_id: int, user_id: int) -> bool:
        """Soft delete a budget"""
        db_budget = self.crud.get_by_id(budget_id=budget_id, user_id=user_id)
        if not db_budget:
            return False

        return self.crud.soft_delete(db_budget=db_budget)

    def update_budget_spent_amount(self, budget_id: int, amount_change: int) -> Optional[Budget]:
        """Update the spent and remaining amounts of a budget"""
        return self.crud.update_spent_amount(budget_id=budget_id, amount_change=amount_change)
    
    def get_budget_summary(self, user_id: int) -> BudgetSummary:
        """Get the summary of all budgets for a user with their transactions"""
        budgets = self.crud.get_multi(user_id=user_id)
        total_spent_amount = sum(budget.spent_amount for budget in budgets) if budgets else 0
        total_remaining_amount = sum(budget.remaining_amount for budget in budgets) if budgets else 0
        total_budget_amount = sum(budget.total_amount for budget in budgets) if budgets else 0
        return BudgetSummary(
            total_spent_amount=total_spent_amount,
            total_remaining_amount=total_remaining_amount,
            total_budget_amount=total_budget_amount,
            budgets=[BudgetSummaryChart(label=budget.name, amount=budget.total_amount, color=budget.color) for budget in budgets]
        )