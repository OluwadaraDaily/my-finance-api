import pytest
from datetime import datetime, timezone, timedelta
from services.budget_service import BudgetService
from schemas.budget import BudgetCreate, BudgetUpdate
from db.models.budget import Budget

def test_create_budget(db_session, test_user, test_category, test_budget_data):
    service = BudgetService(db_session)
    budget_data = BudgetCreate(
        **test_budget_data,
        category_id=test_category.id
    )
    
    budget = service.create_budget(test_user.id, budget_data)
    
    assert budget.name == test_budget_data["name"]
    assert budget.description == test_budget_data["description"]
    assert budget.total_amount == test_budget_data["total_amount"]
    assert budget.spent_amount == 0
    assert budget.remaining_amount == test_budget_data["total_amount"]
    assert budget.user_id == test_user.id
    assert budget.category_id == test_category.id
    assert budget.is_active is True
    assert budget.is_deleted is False

def test_get_budgets(db_session, test_user, test_budget):
    service = BudgetService(db_session)
    budgets = service.get_budgets(test_user.id)
    
    assert len(budgets) == 1
    assert budgets[0].id == test_budget.id
    assert budgets[0].name == test_budget.name

def test_get_budget_by_id(db_session, test_user, test_budget):
    service = BudgetService(db_session)
    budget = service.get_budget_by_id(test_budget.id, test_user.id)
    
    assert budget is not None
    assert budget.id == test_budget.id
    assert budget.name == test_budget.name

def test_get_budget_by_id_not_found(db_session, test_user):
    service = BudgetService(db_session)
    budget = service.get_budget_by_id(999, test_user.id)
    
    assert budget is None

def test_update_budget(db_session, test_user, test_budget):
    service = BudgetService(db_session)
    update_data = BudgetUpdate(
        name="Updated Budget",
        total_amount=1500
    )
    
    updated_budget = service.update_budget(test_budget.id, test_user.id, update_data)
    
    assert updated_budget is not None
    assert updated_budget.name == "Updated Budget"
    assert updated_budget.total_amount == 1500
    assert updated_budget.remaining_amount == 1500  # Should be recalculated

def test_update_budget_not_found(db_session, test_user):
    service = BudgetService(db_session)
    update_data = BudgetUpdate(name="Updated Budget")
    
    updated_budget = service.update_budget(999, test_user.id, update_data)
    
    assert updated_budget is None

def test_delete_budget(db_session, test_user, test_budget):
    service = BudgetService(db_session)
    result = service.delete_budget(test_budget.id, test_user.id)
    
    assert result is True
    
    # Verify the budget is soft deleted
    deleted_budget = service.get_budget_by_id(test_budget.id, test_user.id)
    assert deleted_budget is None
    
    # Verify it exists in DB but is marked as deleted
    budget = db_session.query(Budget).filter_by(id=test_budget.id).first()
    assert budget is not None
    assert budget.is_deleted is True
    assert budget.is_active is False

def test_delete_budget_not_found(db_session, test_user):
    service = BudgetService(db_session)
    result = service.delete_budget(999, test_user.id)
    
    assert result is False

def test_update_budget_spent_amount(db_session, test_user, test_budget):
    service = BudgetService(db_session)
    
    # Add spending
    budget = service.update_budget_spent_amount(test_budget.id, 500)
    assert budget.spent_amount == 500
    assert budget.remaining_amount == 500  # 1000 - 500
    
    # Add more spending
    budget = service.update_budget_spent_amount(test_budget.id, 200)
    assert budget.spent_amount == 700
    assert budget.remaining_amount == 300  # 1000 - 700

def test_update_budget_spent_amount_not_found(db_session):
    service = BudgetService(db_session)
    result = service.update_budget_spent_amount(999, 500)
    
    assert result is None 