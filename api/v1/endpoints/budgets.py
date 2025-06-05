from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from core.deps import get_current_user
from db.models.user import User
from db.session import get_db
from sqlalchemy.orm import Session
from services.budget_service import BudgetService
from schemas.budget import Budget, BudgetCreate, BudgetUpdate
from schemas.common import ResponseModel, ListResponseModel

router = APIRouter()

@router.post("/", response_model=ResponseModel[Budget], status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget"""
    budget_service = BudgetService(db)
    budget = budget_service.create_budget(current_user.id, budget_data)
    return ResponseModel[Budget](
        data=budget,
        message="Budget created successfully"
    )

@router.get("/", response_model=ListResponseModel[Budget])
async def get_budgets(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for the current user"""
    budget_service = BudgetService(db)
    budgets = budget_service.get_budgets(current_user.id, skip=skip, limit=limit)
    return ListResponseModel[Budget](
        data=budgets,
        message="Budgets fetched successfully"
    )

@router.get("/{budget_id}", response_model=ResponseModel[Budget])
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific budget by ID"""
    budget_service = BudgetService(db)
    budget = budget_service.get_budget_by_id(budget_id, current_user.id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    return ResponseModel[Budget](
        data=budget,
        message="Budget fetched successfully"
    )

@router.put("/{budget_id}", response_model=ResponseModel[Budget])
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a budget"""
    budget_service = BudgetService(db)
    budget = budget_service.update_budget(budget_id, current_user.id, budget_data)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    return ResponseModel[Budget](
        data=budget,
        message="Budget updated successfully"
    )

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a budget"""
    budget_service = BudgetService(db)
    deleted = budget_service.delete_budget(budget_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    return None