import pytest
from fastapi import status

def test_create_pot(client, auth_headers, test_pot_data):
    response = client.post("/api/v1/pots/", json=test_pot_data, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    pot = response_data["data"]
    assert pot["name"] == test_pot_data["name"]
    assert pot["description"] == test_pot_data["description"]
    assert pot["target_amount"] == test_pot_data["target_amount"]
    assert pot["color"] == test_pot_data["color"]
    assert pot["saved_amount"] == 0

def test_create_pot_duplicate_name(client, auth_headers, test_pot, test_pot_data):
    response = client.post("/api/v1/pots/", json=test_pot_data, headers=auth_headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Pot already exists" in response.json()["detail"]

def test_get_pots(client, auth_headers, test_pot):
    response = client.get("/api/v1/pots/", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pots = response_data["data"]
    assert len(pots) == 1
    assert pots[0]["id"] == test_pot.id
    assert pots[0]["name"] == test_pot.name

def test_get_pot_by_id(client, auth_headers, test_pot):
    response = client.get(f"/api/v1/pots/{test_pot.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pot = response_data["data"]
    assert pot["id"] == test_pot.id
    assert pot["name"] == test_pot.name
    assert pot["description"] == test_pot.description
    assert pot["target_amount"] == test_pot.target_amount
    assert pot["saved_amount"] == test_pot.saved_amount
    assert pot["color"] == test_pot.color

def test_get_pot_by_id_not_found(client, auth_headers):
    response = client.get("/api/v1/pots/999", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Pot not found" in response.json()["detail"]

def test_update_pot(client, auth_headers, test_pot):
    update_data = {
        "name": "Updated Pot",
        "target_amount": 1500,
        "color": "#0000FF"
    }
    
    response = client.put(
        f"/api/v1/pots/{test_pot.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pot = response_data["data"]
    assert pot["name"] == update_data["name"]
    assert pot["target_amount"] == update_data["target_amount"]
    assert pot["color"] == update_data["color"]
    # Unchanged fields should remain the same
    assert pot["description"] == test_pot.description

def test_delete_pot(client, auth_headers, test_pot):
    response = client.delete(f"/api/v1/pots/{test_pot.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] is True
    
    # Verify pot is deleted
    get_response = client.get(f"/api/v1/pots/{test_pot.id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_update_saved_amount(client, auth_headers, test_pot):
    # Add to saved amount
    response = client.patch(
        f"/api/v1/pots/{test_pot.id}/update-saved-amount",
        json={"amount": 500},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pot = response_data["data"]
    assert pot["saved_amount"] == 500
    
    # Add more to saved amount
    response = client.patch(
        f"/api/v1/pots/{test_pot.id}/update-saved-amount",
        json={"amount": 200},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pot = response_data["data"]
    assert pot["saved_amount"] == 700
    
    # Subtract from saved amount
    response = client.patch(
        f"/api/v1/pots/{test_pot.id}/update-saved-amount",
        json={"amount": -300},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pot = response_data["data"]
    assert pot["saved_amount"] == 400

def test_update_saved_amount_negative_balance(client, auth_headers, test_pot):
    response = client.patch(
        f"/api/v1/pots/{test_pot.id}/update-saved-amount",
        json={"amount": -1000},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot reduce saved amount below zero" in response.json()["detail"] 