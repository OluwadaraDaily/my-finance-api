import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status

def test_create_budget(client, auth_headers, test_category, test_budget_data, db_session):
    # Ensure category is attached to session
    db_session.add(test_category)
    db_session.refresh(test_category)
    category_id = test_category.id
    
    data = {**test_budget_data, "category_id": category_id}
    response = client.post("/api/v1/budgets/", json=data, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    budget = response_data["data"]
    assert budget["name"] == data["name"]
    assert budget["description"] == data["description"]
    assert budget["total_amount"] == data["total_amount"]
    assert budget["category_id"] == category_id
    assert budget["spent_amount"] == 0
    assert budget["remaining_amount"] == data["total_amount"]
    assert budget["is_active"] is True
    assert budget["is_deleted"] is False

def test_create_budget_invalid_data(client, auth_headers, test_category):
    # Missing required fields
    data = {"name": "Test Budget"}
    response = client.post("/api/v1/budgets/", json=data, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_budgets(client, auth_headers, test_budget):
    response = client.get("/api/v1/budgets/", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    budgets = response_data["data"]
    assert len(budgets) == 1
    assert budgets[0]["id"] == test_budget.id
    assert budgets[0]["name"] == test_budget.name

def test_get_budget_by_id(client, auth_headers, test_budget):
    response = client.get(f"/api/v1/budgets/{test_budget.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    budget = response_data["data"]
    assert budget["id"] == test_budget.id
    assert budget["name"] == test_budget.name

def test_get_budget_by_id_not_found(client, auth_headers):
    response = client.get("/api/v1/budgets/999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_budget(client, auth_headers, test_budget):
    update_data = {
        "name": "Updated Budget",
        "total_amount": 1500
    }
    response = client.put(
        f"/api/v1/budgets/{test_budget.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    budget = response_data["data"]
    assert budget["name"] == update_data["name"]
    assert budget["total_amount"] == update_data["total_amount"]
    assert budget["remaining_amount"] == update_data["total_amount"]

def test_update_budget_not_found(client, auth_headers):
    update_data = {"name": "Updated Budget"}
    response = client.put(
        "/api/v1/budgets/999",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_budget(client, auth_headers, test_budget, db_session):
    # Ensure the budget is attached to the session
    db_session.add(test_budget)
    db_session.refresh(test_budget)
    budget_id = test_budget.id
    
    response = client.delete(
        f"/api/v1/budgets/{budget_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the budget is no longer accessible
    response = client.get(
        f"/api/v1/budgets/{budget_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_budget_not_found(client, auth_headers):
    response = client.delete("/api/v1/budgets/999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_unauthorized_access(client, test_budget):
    # Try to access without auth headers
    endpoints = [
        ("GET", "/api/v1/budgets/"),
        ("GET", f"/api/v1/budgets/{test_budget.id}"),
        ("POST", "/api/v1/budgets/"),
        ("PUT", f"/api/v1/budgets/{test_budget.id}"),
        ("DELETE", f"/api/v1/budgets/{test_budget.id}")
    ]
    
    for method, endpoint in endpoints:
        response = client.request(method, endpoint)
        # Accept either 401 Unauthorized or 403 Forbidden as both indicate auth failure
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN] 