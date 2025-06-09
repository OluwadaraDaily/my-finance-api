import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from schemas.transaction import TransactionType

def test_create_transaction(client, auth_headers, test_transaction_data):
    response = client.post(
        "/api/v1/transactions/",
        json=test_transaction_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    transaction = response_data["data"]
    assert transaction["description"] == test_transaction_data["description"]
    assert transaction["amount"] == test_transaction_data["amount"]
    assert transaction["type"] == test_transaction_data["type"]
    assert transaction["meta_data"] == test_transaction_data["meta_data"]

def test_get_transactions(client, auth_headers, test_transaction_data):
    # Create test transactions
    response = client.post(
        "/api/v1/transactions/",
        json=test_transaction_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Create another transaction with different data
    test_transaction_data_2 = {
        **test_transaction_data,
        "amount": 2000,
        "type": "CREDIT"
    }
    response = client.post(
        "/api/v1/transactions/",
        json=test_transaction_data_2,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Test basic retrieval
    response = client.get(
        f"/api/v1/transactions/?account_id={test_transaction_data['account_id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["data"]) == 2

    # Test sorting
    response = client.get(
        f"/api/v1/transactions/?account_id={test_transaction_data['account_id']}&sort_by=amount&sort_order=asc",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    transactions = response_data["data"]
    assert transactions[0]["amount"] == 1000
    assert transactions[1]["amount"] == 2000

    # Test filtering
    response = client.get(
        f"/api/v1/transactions/?account_id={test_transaction_data['account_id']}&type=CREDIT&min_amount=1500&max_amount=2500",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    transactions = response_data["data"]
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 2000
    assert transactions[0]["type"] == "CREDIT"

def test_get_transaction(client, auth_headers, test_transaction_data):
    # Create a test transaction
    response = client.post(
        "/api/v1/transactions/",
        json=test_transaction_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]

    # Get the transaction by ID
    response = client.get(
        f"/api/v1/transactions/{created_transaction['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    transaction = response_data["data"]
    assert transaction["id"] == created_transaction["id"]
    assert transaction["description"] == test_transaction_data["description"]

def test_get_transaction_not_found(client, auth_headers, test_account):
    response = client.get(
        f"/api/v1/transactions/999?account_id={test_account.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Transaction not found" in response.json()["detail"]

def test_update_transaction(client, auth_headers, test_transaction_data):
    # Create a test transaction
    response = client.post(
        "/api/v1/transactions/",
        json=test_transaction_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]

    # Update the transaction
    update_data = {
        "description": "Updated Transaction",
        "amount": 1500,
        "type": "CREDIT"
    }
    response = client.put(
        f"/api/v1/transactions/{created_transaction['id']}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    transaction = response_data["data"]
    assert transaction["description"] == "Updated Transaction"
    assert transaction["amount"] == 1500
    assert transaction["type"] == "CREDIT"
    # Unchanged fields should remain the same
    assert transaction["meta_data"] == test_transaction_data["meta_data"]

def test_delete_transaction(client, auth_headers, test_transaction_data):
    # Create a test transaction
    response = client.post(
        "/api/v1/transactions/",
        json=test_transaction_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]

    # Delete the transaction
    response = client.delete(
        f"/api/v1/transactions/{created_transaction['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] is True

    # Verify the transaction is deleted
    response = client.get(
        f"/api/v1/transactions/{created_transaction['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_transaction_summary(client, auth_headers, test_transaction_data):
    # Create test transactions with different amounts and types
    transactions_data = [
        {
            **test_transaction_data,
            "amount": 1000,
            "type": "CREDIT",
            "transaction_date": datetime.now(timezone.utc).isoformat()
        },
        {
            **test_transaction_data,
            "amount": 500,
            "type": "DEBIT",
            "transaction_date": datetime.now(timezone.utc).isoformat()
        },
        {
            **test_transaction_data,
            "amount": 1500,
            "type": "CREDIT",
            "transaction_date": datetime.now(timezone.utc).isoformat()
        },
        {
            **test_transaction_data,
            "amount": 700,
            "type": "DEBIT",
            "transaction_date": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for transaction_data in transactions_data:
        response = client.post(
            "/api/v1/transactions/",
            json=transaction_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED

    # Test summary calculation without date filters
    response = client.get(
        "/api/v1/transactions/summary",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    summary = response_data["data"]
    assert summary["total_transactions"] == 4
    assert summary["total_income"] == 2500
    assert summary["total_expense"] == 1200
    assert summary["net_amount"] == 1300

    # Test summary with date filters
    future_date = datetime.now(timezone.utc) + timedelta(days=1)
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    
    # Format dates in the exact format that works with the API
    future_date_str = future_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    past_date_str = past_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    response = client.get(
        "/api/v1/transactions/summary"
        f"?start_date={past_date_str}&end_date={future_date_str}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    summary = response_data["data"]
    assert summary["total_transactions"] == 4
    assert summary["total_income"] == 2500
    assert summary["total_expense"] == 1200
    assert summary["net_amount"] == 1300

def test_create_transaction_with_account_update(client, auth_headers, test_account, test_category):
    initial_balance = test_account.balance
    
    # Create a DEBIT transaction
    debit_data = {
        "account_id": test_account.id,
        "category_id": test_category.id,
        "description": "Test Debit Transaction",
        "amount": 1000,
        "type": "DEBIT",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=debit_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]
    assert created_transaction["amount"] == 1000
    assert created_transaction["type"] == "DEBIT"
    
    # Verify account balance was updated
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == status.HTTP_200_OK
    account_data = account_response.json()["data"]
    assert account_data["balance"] == initial_balance - 1000
    
    # Create a CREDIT transaction
    credit_data = {
        "account_id": test_account.id,
        "category_id": test_category.id,
        "description": "Test Credit Transaction",
        "amount": 2000,
        "type": "CREDIT",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=credit_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]
    assert created_transaction["amount"] == 2000
    assert created_transaction["type"] == "CREDIT"
    
    # Verify account balance was updated
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == status.HTTP_200_OK
    account_data = account_response.json()["data"]
    assert account_data["balance"] == initial_balance - 1000 + 2000

def test_update_transaction_with_account_update(client, auth_headers, test_account, test_category):
    initial_balance = test_account.balance  # Should be 5000
    
    # First create a transaction
    transaction_data = {
        "account_id": test_account.id,
        "category_id": test_category.id,
        "description": "Test Transaction",
        "amount": 1000,
        "type": "DEBIT",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=transaction_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]
    
    # After DEBIT of 1000, balance should be 4000
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == status.HTTP_200_OK
    account_data = account_response.json()["data"]
    assert account_data["balance"] == initial_balance - 1000  # 4000
    
    # Update the transaction from DEBIT 1000 to CREDIT 1500
    update_data = {
        "type": "CREDIT",
        "amount": 1500
    }
    
    response = client.put(
        f"/api/v1/transactions/{created_transaction['id']}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    updated_transaction = response.json()["data"]
    assert updated_transaction["type"] == "CREDIT"
    assert updated_transaction["amount"] == 1500
    
    # Final balance calculation:
    # Initial: 5000
    # After DEBIT 1000: 4000
    # Revert DEBIT 1000: 5000
    # Apply CREDIT 1500: 6500
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == status.HTTP_200_OK
    account_data = account_response.json()["data"]
    expected_balance = initial_balance + 1500  # 5000 + 1500 = 6500
    assert account_data["balance"] == expected_balance

def test_delete_transaction_with_account_update(client, auth_headers, test_account, test_category):
    initial_balance = test_account.balance
    
    # First create a transaction
    transaction_data = {
        "account_id": test_account.id,
        "category_id": test_category.id,
        "description": "Test Transaction",
        "amount": 1000,
        "type": "DEBIT",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=transaction_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_transaction = response.json()["data"]
    
    # Verify initial account balance update
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == status.HTTP_200_OK
    account_data = account_response.json()["data"]
    assert account_data["balance"] == initial_balance - 1000
    
    # Delete the transaction
    response = client.delete(
        f"/api/v1/transactions/{created_transaction['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Verify account balance was restored
    account_response = client.get(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers
    )
    assert account_response.status_code == status.HTTP_200_OK
    account_data = account_response.json()["data"]
    assert account_data["balance"] == initial_balance 