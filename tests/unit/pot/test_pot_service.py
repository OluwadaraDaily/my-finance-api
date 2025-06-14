import pytest
from datetime import datetime
from services.pot_service import PotService
from schemas.pot import PotCreate, PotUpdate
from db.models.pots import Pot
from fastapi import HTTPException
from db.models.transaction import Transaction
from schemas.transaction import TransactionType

@pytest.fixture
def test_pot_data():
    return {
        "name": "Test Pot",
        "description": "Test Pot Description",
        "target_amount": 1000,
        "color": "#FF0000"
    }

@pytest.fixture
def test_pot(db_session, test_user):
    pot = Pot(
        name="Test Pot",
        description="Test Pot Description",
        target_amount=1000,
        saved_amount=0,
        color="#FF0000",
        user_id=test_user.id
    )
    db_session.add(pot)
    db_session.commit()
    db_session.refresh(pot)
    return pot

def test_create_pot(db_session, test_user, test_pot_data):
    service = PotService(db_session)
    pot_data = PotCreate(**test_pot_data)
    
    pot = service.create_pot(test_user.id, pot_data)
    
    assert pot.name == test_pot_data["name"]
    assert pot.description == test_pot_data["description"]
    assert pot.target_amount == test_pot_data["target_amount"]
    assert pot.saved_amount == 0
    assert pot.color == test_pot_data["color"]
    assert pot.user_id == test_user.id

def test_create_pot_duplicate_name(db_session, test_user, test_pot):
    service = PotService(db_session)
    pot_data = PotCreate(
        name=test_pot.name,
        description="Another description",
        target_amount=2000,
        color="#00FF00"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.create_pot(test_user.id, pot_data)
    assert exc_info.value.status_code == 400
    assert "Pot already exists" in str(exc_info.value.detail)

def test_get_pots(db_session, test_user):
    service = PotService(db_session)
    
    # Create test pots
    pot1 = Pot(name="Test Pot 1", target_amount=1000, user_id=test_user.id)
    pot2 = Pot(name="Test Pot 2", target_amount=2000, user_id=test_user.id)
    db_session.add_all([pot1, pot2])
    db_session.commit()

    # Get pots
    pots = service.get_pots(test_user.id)
    assert len(pots) == 2
    assert pots[0].name == "Test Pot 1"
    assert pots[1].name == "Test Pot 2"
    assert all(pot.user_id == test_user.id for pot in pots)

def test_get_pot_by_id(db_session, test_user, test_pot):
    service = PotService(db_session)
    pot = service.get_pot_by_id(test_pot.id, test_user.id)
    
    assert pot is not None
    assert pot.id == test_pot.id
    assert pot.name == test_pot.name

def test_get_pot_by_id_not_found(db_session, test_user):
    service = PotService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_pot_by_id(999, test_user.id)
    assert exc_info.value.status_code == 404
    assert "Pot not found" in str(exc_info.value.detail)

def test_update_pot(db_session, test_user, test_pot):
    service = PotService(db_session)
    update_data = PotUpdate(
        name="Updated Pot",
        target_amount=1500,
        color="#0000FF"
    )
    
    updated_pot = service.update_pot(test_pot.id, test_user.id, update_data)
    
    assert updated_pot is not None
    assert updated_pot.name == "Updated Pot"
    assert updated_pot.target_amount == 1500
    assert updated_pot.color == "#0000FF"
    # Unchanged fields should remain the same
    assert updated_pot.description == test_pot.description

def test_delete_pot(db_session, test_user, test_pot):
    service = PotService(db_session)
    result = service.delete_pot(test_pot.id, test_user.id)
    
    assert result is True
    
    # Verify the pot is deleted
    deleted_pot = db_session.query(Pot).filter_by(id=test_pot.id).first()
    assert deleted_pot is None

def test_update_saved_amount(db_session, test_user, test_pot):
    service = PotService(db_session)
    initial_balance = test_user.account.balance
    
    # Add to saved amount
    pot = service.update_saved_amount(test_pot.id, test_user.id, test_user, 500, "Initial savings deposit")
    assert pot.saved_amount == 500
    
    # Verify transaction was created and account balance updated
    transaction = db_session.query(Transaction).filter_by(pot_id=test_pot.id).first()
    assert transaction is not None
    assert transaction.amount == 500
    assert transaction.description == "Initial savings deposit"
    assert transaction.type == TransactionType.CREDIT
    assert test_user.account.balance == initial_balance + 500
    
    # Add more to saved amount
    pot = service.update_saved_amount(test_pot.id, test_user.id, test_user, 200, "Additional savings")
    assert pot.saved_amount == 700
    assert test_user.account.balance == initial_balance + 700
    
    # Subtract from saved amount
    pot = service.update_saved_amount(test_pot.id, test_user.id, test_user, -300, "Emergency withdrawal")
    assert pot.saved_amount == 400
    assert test_user.account.balance == initial_balance + 400
    
    # Verify all transactions exist
    transactions = db_session.query(Transaction).filter_by(pot_id=test_pot.id).all()
    assert len(transactions) == 3
    
    # Verify the withdrawal transaction
    withdrawal = [t for t in transactions if t.amount < 0][0]
    assert withdrawal.amount == -300
    assert withdrawal.description == "Emergency withdrawal"
    assert withdrawal.type == TransactionType.DEBIT

def test_update_saved_amount_negative_balance(db_session, test_user, test_pot):
    service = PotService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.update_saved_amount(test_pot.id, test_user.id, test_user, -1000, "Attempt to withdraw too much")
    assert "Cannot reduce saved amount below zero" in str(exc_info.value.detail) 