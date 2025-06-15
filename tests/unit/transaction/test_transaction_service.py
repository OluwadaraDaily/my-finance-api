import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from services.transaction_service import TransactionService
from schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilter, TransactionType
from db.models.transaction import Transaction
from db.models.category import Category
from db.models.budget import Budget
from db.models.pots import Pot

def test_create_transaction(db_session, test_transaction_data, test_user, test_category):
    service = TransactionService(db_session)
    transaction_data = TransactionCreate(
        account_id=test_transaction_data["account_id"],
        category_id=test_category.id,
        description="Test Transaction",
        amount=1000,
        type=TransactionType.DEBIT,
        user_id=test_user.id,
        transaction_date=datetime.now(timezone.utc)
    )
    
    transaction = service.create_transaction(transaction_data, test_user)
    
    assert transaction.description == transaction_data.description
    assert transaction.amount == transaction_data.amount
    assert transaction.type == transaction_data.type
    assert transaction.category_id == test_category.id

def test_get_transactions(db_session, test_transaction_data, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create multiple test transactions
    transaction1 = Transaction(
        account_id=test_user.account.id,
        category_id=test_category.id,
        description="Test Transaction 1",
        amount=1000,
        type=TransactionType.DEBIT,
        user_id=test_user.id,
        transaction_date=datetime.now(timezone.utc)
    )
    transaction2 = Transaction(
        account_id=test_user.account.id,
        category_id=test_category.id,
        description="Test Transaction 2",
        amount=2000,
        type=TransactionType.CREDIT,
        user_id=test_user.id,
        transaction_date=datetime.now(timezone.utc)
    )
    db_session.add_all([transaction1, transaction2])
    db_session.commit()

    # Test basic retrieval
    transactions = service.get_transactions(account_id=test_user.account.id)
    assert len(transactions) == 2

    # Test sorting
    transactions = service.get_transactions(
        account_id=test_user.account.id,
        sort_by="amount",
        sort_order="asc"
    )
    assert transactions[0].amount == 1000
    assert transactions[1].amount == 2000

    # Test filtering
    filters = TransactionFilter(
        type=TransactionType.CREDIT,
        min_amount=1500,
        max_amount=2500
    )
    transactions = service.get_transactions(
        account_id=test_user.account.id,
        filters=filters
    )
    assert len(transactions) == 1
    assert transactions[0].amount == 2000
    assert transactions[0].type == TransactionType.CREDIT

def test_get_transaction_by_id(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create a test transaction first
    transaction = Transaction(
        account_id=test_user.account.id,
        category_id=test_category.id,
        description="Test Transaction",
        amount=1000,
        type=TransactionType.DEBIT,
        user_id=test_user.id,
        transaction_date=datetime.now(timezone.utc)
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    # Test retrieval
    retrieved_transaction = service.get_transaction_by_id(transaction.id, transaction.account_id)
    assert retrieved_transaction is not None
    assert retrieved_transaction.id == transaction.id
    assert retrieved_transaction.description == transaction.description

def test_get_transaction_by_id_not_found(db_session):
    service = TransactionService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_transaction_by_id(999, 1)
    assert exc_info.value.status_code == 404
    assert "Transaction not found" in str(exc_info.value.detail)

def test_update_transaction_with_account_update(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create a test transaction first
    transaction = Transaction(
        account_id=test_user.account.id,
        category_id=test_category.id,
        description="Test Transaction",
        amount=1000,
        type=TransactionType.DEBIT,
        user_id=test_user.id,
        transaction_date=datetime.now(timezone.utc)
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    initial_balance = test_user.account.balance
    
    # Update transaction from DEBIT to CREDIT
    update_data = TransactionUpdate(
        type=TransactionType.CREDIT,
        amount=1500
    )
    
    updated_transaction = service.update_transaction(
        transaction.id,
        test_user.account.id,
        update_data
    )
    db_session.refresh(test_user.account)
    
    assert updated_transaction.type == TransactionType.CREDIT
    assert updated_transaction.amount == 1500
    # Original debit of 1000 is reverted (+1000) and new credit of 1500 is applied (+1500)
    assert test_user.account.balance == initial_balance + 1000 + 1500

def test_delete_transaction_with_account_update(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create a test transaction first
    transaction = Transaction(
        account_id=test_user.account.id,
        category_id=test_category.id,
        description="Test Transaction",
        amount=1000,
        type=TransactionType.DEBIT,
        user_id=test_user.id,
        transaction_date=datetime.now(timezone.utc)
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    initial_balance = test_user.account.balance
    
    result = service.delete_transaction(transaction.id, test_user.account.id)
    db_session.refresh(test_user.account)
    
    assert result is True
    # Original debit of 1000 should be reverted
    assert test_user.account.balance == initial_balance + 1000
    
    # Verify the transaction is deleted
    deleted_transaction = db_session.query(Transaction).filter_by(id=transaction.id).first()
    assert deleted_transaction is None

def test_get_transaction_summary(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create test transactions with different amounts and types
    transactions = [
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Test Credit 1",
            amount=1000,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Test Debit 1",
            amount=500,
            type=TransactionType.DEBIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Test Credit 2",
            amount=1500,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Test Debit 2",
            amount=700,
            type=TransactionType.DEBIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        )
    ]
    db_session.add_all(transactions)
    db_session.commit()

    # Test summary calculation
    summary = service.get_transaction_summary(account_id=test_user.account.id)
    assert summary["total_transactions"] == 4
    assert summary["total_income"] == 2500
    assert summary["total_expense"] == 1200
    assert summary["net_amount"] == 1300

    # Test summary with date filters
    future_date = datetime.now(timezone.utc) + timedelta(days=1)
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    
    summary = service.get_transaction_summary(
        account_id=test_user.account.id,
        start_date=past_date,
        end_date=future_date
    )
    assert summary["total_transactions"] == 4
    assert summary["total_income"] == 2500
    assert summary["total_expense"] == 1200
    assert summary["net_amount"] == 1300

def test_get_transactions_by_budget(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create test budgets first
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=30)
    
    budget_1 = Budget(
        user_id=test_user.id,
        category_id=test_category.id,
        name="Test Budget 1",
        description="Test Budget 1 Description",
        total_amount=1000,
        spent_amount=0,
        remaining_amount=1000,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    budget_2 = Budget(
        user_id=test_user.id,
        category_id=test_category.id,
        name="Test Budget 2",
        description="Test Budget 2 Description",
        total_amount=2000,
        spent_amount=0,
        remaining_amount=2000,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    db_session.add_all([budget_1, budget_2])
    db_session.commit()
    
    # Create test transactions
    transactions = [
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Budget 1 Transaction 1",
            amount=1000,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            budget_id=budget_1.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Budget 1 Transaction 2",
            amount=500,
            type=TransactionType.DEBIT,
            user_id=test_user.id,
            budget_id=budget_1.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Budget 2 Transaction",
            amount=1500,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            budget_id=budget_2.id,
            transaction_date=datetime.now(timezone.utc)
        )
    ]
    db_session.add_all(transactions)
    db_session.commit()

    # Test retrieving transactions for budget_1
    budget_1_transactions = service.get_transactions_by_budget(budget_id=budget_1.id, account_id=test_user.account.id)
    assert len(budget_1_transactions) == 2
    assert all(t.budget_id == budget_1.id for t in budget_1_transactions)
    
    # Test retrieving transactions for budget_2
    budget_2_transactions = service.get_transactions_by_budget(budget_id=budget_2.id, account_id=test_user.account.id)
    assert len(budget_2_transactions) == 1
    assert budget_2_transactions[0].budget_id == budget_2.id

def test_get_transactions_by_pot(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create test pots first
    pot_1 = Pot(
        name="Test Pot 1",
        description="Test Pot 1 Description",
        target_amount=1000,
        saved_amount=0,
        color="#FF0000",
        user_id=test_user.id
    )
    pot_2 = Pot(
        name="Test Pot 2",
        description="Test Pot 2 Description",
        target_amount=2000,
        saved_amount=0,
        color="#00FF00",
        user_id=test_user.id
    )
    db_session.add_all([pot_1, pot_2])
    db_session.commit()
    
    # Create test transactions
    transactions = [
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Pot 1 Transaction 1",
            amount=1000,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            pot_id=pot_1.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Pot 1 Transaction 2",
            amount=500,
            type=TransactionType.DEBIT,
            user_id=test_user.id,
            pot_id=pot_1.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Pot 2 Transaction",
            amount=1500,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            pot_id=pot_2.id,
            transaction_date=datetime.now(timezone.utc)
        )
    ]
    db_session.add_all(transactions)
    db_session.commit()

    # Test retrieving transactions for pot_1
    pot_1_transactions = service.get_transactions_by_pot(pot_id=pot_1.id, account_id=test_user.account.id)
    assert len(pot_1_transactions) == 2
    assert all(t.pot_id == pot_1.id for t in pot_1_transactions)
    
    # Test retrieving transactions for pot_2
    pot_2_transactions = service.get_transactions_by_pot(pot_id=pot_2.id, account_id=test_user.account.id)
    assert len(pot_2_transactions) == 1
    assert pot_2_transactions[0].pot_id == pot_2.id

def test_get_transactions_by_category(db_session, test_user, test_category):
    service = TransactionService(db_session)
    
    # Create a second test category
    test_category_2 = Category(
        name="Test Category 2",
        description="Test Category 2 Description",
        user_id=test_user.id
    )
    db_session.add(test_category_2)
    db_session.commit()
    
    # Create test transactions
    transactions = [
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Category 1 Transaction 1",
            amount=1000,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category.id,
            description="Category 1 Transaction 2",
            amount=500,
            type=TransactionType.DEBIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        ),
        Transaction(
            account_id=test_user.account.id,
            category_id=test_category_2.id,
            description="Category 2 Transaction",
            amount=1500,
            type=TransactionType.CREDIT,
            user_id=test_user.id,
            transaction_date=datetime.now(timezone.utc)
        )
    ]
    db_session.add_all(transactions)
    db_session.commit()

    # Test retrieving transactions for test_category
    category_1_transactions = service.get_transactions_by_category(category_id=test_category.id, account_id=test_user.account.id)
    assert len(category_1_transactions) == 2
    assert all(t.category_id == test_category.id for t in category_1_transactions)
    
    # Test retrieving transactions for test_category_2
    category_2_transactions = service.get_transactions_by_category(category_id=test_category_2.id, account_id=test_user.account.id)
    assert len(category_2_transactions) == 1
    assert category_2_transactions[0].category_id == test_category_2.id

def test_budget_amount_updates(db_session, test_user, test_category):
    """Test that budget amounts are correctly updated when transactions change"""
    service = TransactionService(db_session)
    
    # Create a test budget
    budget = Budget(
        user_id=test_user.id,
        name="Test Budget",
        description="Test Budget Description",
        total_amount=10000,  # $100.00
        spent_amount=0,
        remaining_amount=10000,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    
    # Test 1: Create a debit transaction
    transaction_data = TransactionCreate(
        description="Test Debit Transaction",
        amount=2000,  # $20.00
        type=TransactionType.DEBIT,
        transaction_date=datetime.now(timezone.utc),
        budget_id=budget.id
    )
    transaction = service.create_transaction(transaction_data, test_user)
    
    # Verify budget amounts after debit
    db_session.refresh(budget)
    assert budget.spent_amount == 2000
    assert budget.remaining_amount == 8000
    
    # Test 2: Create a credit transaction
    credit_transaction_data = TransactionCreate(
        description="Test Credit Transaction",
        amount=1000,  # $10.00
        type=TransactionType.CREDIT,
        transaction_date=datetime.now(timezone.utc),
        budget_id=budget.id
    )
    credit_transaction = service.create_transaction(credit_transaction_data, test_user)
    
    # Verify budget amounts after credit
    db_session.refresh(budget)
    assert budget.spent_amount == 1000  # 2000 - 1000
    assert budget.remaining_amount == 9000
    
    # Test 3: Update transaction amount
    update_data = TransactionUpdate(amount=3000)  # $30.00
    updated_transaction = service.update_transaction(
        transaction_id=transaction.id,
        account_id=test_user.account.id,
        transaction_data=update_data
    )
    
    # Verify budget amounts after update
    db_session.refresh(budget)
    assert budget.spent_amount == 2000  # 3000 - 1000
    assert budget.remaining_amount == 8000
    
    # Test 4: Delete a transaction
    service.delete_transaction(transaction.id, test_user.account.id)
    
    # Verify budget amounts after deletion
    db_session.refresh(budget)
    assert budget.spent_amount == -1000  # Only the credit transaction remains
    assert budget.remaining_amount == 10000  # Should be reset to total_amount since spent_amount would be negative

def test_budget_change_in_transaction(db_session, test_user, test_category):
    """Test that budget amounts are correctly updated when a transaction's budget is changed"""
    service = TransactionService(db_session)
    
    # Create two test budgets
    budget1 = Budget(
        user_id=test_user.id,
        name="Budget 1",
        description="Budget 1 Description",
        total_amount=10000,
        spent_amount=0,
        remaining_amount=10000,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True
    )
    budget2 = Budget(
        user_id=test_user.id,
        name="Budget 2",
        description="Budget 2 Description",
        total_amount=20000,
        spent_amount=0,
        remaining_amount=20000,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True
    )
    db_session.add_all([budget1, budget2])
    db_session.commit()
    db_session.refresh_all([budget1, budget2])
    
    # Create a transaction with budget1
    transaction_data = TransactionCreate(
        description="Test Transaction",
        amount=5000,
        type=TransactionType.DEBIT,
        transaction_date=datetime.now(timezone.utc),
        budget_id=budget1.id
    )
    transaction = service.create_transaction(transaction_data, test_user)
    
    # Verify budget1 amounts
    db_session.refresh(budget1)
    assert budget1.spent_amount == 5000
    assert budget1.remaining_amount == 5000
    
    # Change transaction to budget2
    update_data = TransactionUpdate(budget_id=budget2.id)
    updated_transaction = service.update_transaction(
        transaction_id=transaction.id,
        account_id=test_user.account.id,
        transaction_data=update_data
    )
    
    # Verify both budgets' amounts
    db_session.refresh_all([budget1, budget2])
    assert budget1.spent_amount == 0
    assert budget1.remaining_amount == 10000
    assert budget2.spent_amount == 5000
    assert budget2.remaining_amount == 15000 