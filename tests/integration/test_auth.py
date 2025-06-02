import pytest
from fastapi import status

def test_login_success(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_protected_route_with_token(client, test_user):
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    token = login_response.json()["data"]["access_token"]
    
    # Test protected route
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"

def test_register_success(client, mocker):
    # Mock the email service
    mock_email_service = mocker.patch('services.email_service.EmailService.send_activation_email')
    
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "username": "newuser"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "data" in data
    assert data["data"]["email"] == "newuser@example.com"
    assert data["data"]["username"] == "newuser"
    
    # Verify the email service was called
    mock_email_service.assert_called_once() 