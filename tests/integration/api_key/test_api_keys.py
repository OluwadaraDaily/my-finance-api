from fastapi import status
from datetime import datetime, timedelta, timezone
from db.models.user import User

def test_create_api_key(client, test_user, auth_headers):
    user_email = test_user.email
    
    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={
            "name": "Test API Key",
            "expires_in_days": 30
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["api_key"]["name"] == "Test API Key"
    assert "raw_key" in data

    response = client.get(
        "/api/v1/api-keys/test",
        headers={"X-API-Key": data["raw_key"]}
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()["data"]
    assert response_data["user"]["email"] == user_email

    # Test expiration date handling
    data["api_key"]["expires_at"] = datetime.now(timezone.utc) - timedelta(days=1)
    response = client.get(
        "/api/v1/api-keys/test",
        headers={"X-API-Key": data["api_key"]["key"]}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Test invalid API key
    response = client.get(
        "/api/v1/api-keys/test",
        headers={"X-API-Key": "invalid"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_api_keys(client, test_user, auth_headers):
    no_of_api_keys = 4
    for i in range(no_of_api_keys):
        response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={
                "name": f"Test API Key {i}",
                "expires_in_days": 30
            }
        )
        assert response.status_code == status.HTTP_200_OK

    response = client.get(
        "/api/v1/api-keys",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data) == no_of_api_keys


def test_list_active_api_keys(client, test_user, auth_headers):
    no_of_api_keys = 4
    api_keys = []
    for i in range(no_of_api_keys):
        response = client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={
                "name": f"Test API Key {i}",
                "expires_in_days": 30
            }
        )
        assert response.status_code == status.HTTP_200_OK
        api_keys.append(response.json()["data"]["api_key"])

    # Get initial count of active keys
    response = client.get(
        "/api/v1/api-keys/active",  # Use active endpoint instead
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    initial_count = len(response.json()["data"])

    # Revoke one key
    response = client.delete(
        f"/api/v1/api-keys/{api_keys[0]['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify the key was deleted using active keys endpoint
    response = client.get(
        "/api/v1/api-keys/active",  # Use active endpoint
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data) == initial_count - 1  # Should have one less active key


