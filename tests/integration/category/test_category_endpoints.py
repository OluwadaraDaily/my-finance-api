from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from db.models.category import Category
from main import app
from core.deps import get_current_user, get_db
from db.models.user import User
from fastapi import status

def test_get_categories(client, auth_headers):
    # Create categories through API
    client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "Test Category 1"}
    )
    client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "Test Category 2"}
    )
    
    response = client.get("/api/v1/categories/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2
    assert data["message"] == "Categories fetched successfully"
    categories = data["data"]
    assert any(cat["name"] == "Test Category 1" for cat in categories)
    assert any(cat["name"] == "Test Category 2" for cat in categories)

def test_create_category(client, auth_headers):
    response = client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "New Category", "color": "#FF0000"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "message" in data
    assert data["message"] == "Category created successfully"
    assert data["data"]["name"] == "New Category"
    assert data["data"]["color"] == "#FF0000"

def test_create_duplicate_category(client, auth_headers):
    # Create first category through API
    client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "Test Category"}
    )

    # Try to create duplicate
    response = client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "Test Category"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Category already exists"

def test_update_category(client, auth_headers):
    # Create category through API
    create_response = client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "Old Name"}
    )
    category_id = create_response.json()["data"]["id"]
    
    response = client.put(
        f"/api/v1/categories/{category_id}",
        headers=auth_headers,
        json={"name": "Updated Category", "color": "#00FF00"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "message" in data
    assert data["message"] == "Category updated successfully"
    assert data["data"]["name"] == "Updated Category"
    assert data["data"]["color"] == "#00FF00"

def test_delete_category(client, auth_headers):
    # Create category through API
    create_response = client.post(
        "/api/v1/categories/",
        headers=auth_headers,
        json={"name": "To Delete"}
    )
    category_id = create_response.json()["data"]["id"]
    
    response = client.delete(
        f"/api/v1/categories/{category_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Category deleted successfully"
    
    # Verify category is deleted through API
    get_response = client.get(
        f"/api/v1/categories/{category_id}",
        headers=auth_headers
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_get_non_existent_category(client, auth_headers):
    response = client.get(
        "/api/v1/categories/999",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Category not found"

def test_update_non_existent_category(client, auth_headers):
    response = client.put(
        "/api/v1/categories/999",
        headers=auth_headers,
        json={"name": "Updated Category"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Category not found"

def test_delete_non_existent_category(client, auth_headers):
    response = client.delete(
        "/api/v1/categories/999",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Category not found" 