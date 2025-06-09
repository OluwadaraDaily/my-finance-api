import pytest
import os
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from db.base import Base
from db.session import get_db
from core.config import settings
from core.security import get_password_hash

# Test configuration
TEST_JWT_SECRET = "test_secret_key_for_testing_123456789"
DATABASE_URL = settings.TEST_DB_URL

# Create test engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Ensures connection is still valid before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    poolclass=StaticPool,
)

# Create all tables once for the test session
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET
    yield
    # Clean up if needed
    if "JWT_SECRET_KEY" in os.environ:
        del os.environ["JWT_SECRET_KEY"]
    # Clean up database at the end of test session
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Provide a clean database session for each test function.
    Instead of dropping all tables, we use transactions to roll back changes."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    from crud.user import UserCRUD
    from schemas.user import UserCreate
    
    user_data = {
        "email": "test@example.com",
        "username": "testuser123"
    }
    hashed_password = get_password_hash("testpassword123")
    user = UserCRUD(db_session).create(UserCreate(**user_data, password=hashed_password))
    db_session.refresh(user)
    return user  # No need for cleanup as we're using transaction rollback

@pytest.fixture(scope="function")
def test_access_token(test_user):
    from core.jwt import create_access_token
    # Create a token that expires far in the future for testing
    expires_delta = timedelta(hours=1)
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=expires_delta,
        secret_key=TEST_JWT_SECRET
    )
    return access_token

@pytest.fixture(scope="function")
def auth_headers(test_access_token):
    """Fixture to provide authentication headers for protected endpoints"""
    return {"Authorization": f"Bearer {test_access_token}"}

@pytest.fixture(scope="function")
def test_active_api_key(db_session, test_user):
    from services.api_key_service import APIKeyService
    api_key_service = APIKeyService(db_session)
    raw_key, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    return raw_key, api_key

@pytest.fixture(scope="function")
def test_expired_api_key(db_session, test_user):
    from services.api_key_service import APIKeyService
    api_key_service = APIKeyService(db_session)
    # Create an API key that expired 5 days ago
    expires_at = datetime.now(timezone.utc) - timedelta(days=5)
    raw_key, api_key = api_key_service.create_api_key(
        user_id=test_user.id,
        name="Test API Key",
        expires_in_days=None
    )
    api_key.expires_at = expires_at
    db_session.commit()
    return raw_key, api_key

@pytest.fixture(scope="function")
def test_revoked_api_key(db_session, test_user):
    from services.api_key_service import APIKeyService
    api_key_service = APIKeyService(db_session)
    raw_key, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    api_key_service.revoke_api_key(api_key.id, test_user.id)
    return raw_key, api_key

@pytest.fixture(scope="function")
def test_api_key_with_no_expiration(db_session, test_user):
    from services.api_key_service import APIKeyService
    api_key_service = APIKeyService(db_session)
    raw_key, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", None)
    return raw_key, api_key

@pytest.fixture(scope="function")
def test_category(db_session, test_user):
    from db.models.category import Category
    category = Category(
        name="Test Category",
        description="Test Category Description",
        user_id=test_user.id
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category

@pytest.fixture(scope="function")
def test_budget(db_session, test_user, test_category):
    from db.models.budget import Budget
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=30)
    
    budget = Budget(
        user_id=test_user.id,
        category_id=test_category.id,
        name="Test Budget",
        description="Test Budget Description",
        total_amount=1000,
        spent_amount=0,
        remaining_amount=1000,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget

@pytest.fixture(scope="function")
def test_budget_data():
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=30)
    
    return {
        "name": "New Test Budget",
        "description": "New Test Budget Description",
        "total_amount": 2000,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }

@pytest.fixture(scope="function")
def test_pot_data():
    return {
        "name": "Test Pot",
        "description": "Test Pot Description",
        "target_amount": 1000,
        "color": "#FF0000"
    }

@pytest.fixture(scope="function")
def test_pot(db_session, test_user):
    from db.models.pots import Pot
    
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
    return pot  # No need for cleanup as we're using transaction rollback

@pytest.fixture(scope="function")
def test_account(db_session, test_user):
    from db.models.account import Account
    account = Account(
        user_id=test_user.id,
        balance=5000  # Initial balance of 5000
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account

@pytest.fixture(scope="function")
def test_transaction_data(test_account, test_user, test_category):
    return {
        "account_id": test_account.id,
        "category_id": test_category.id,
        "description": "Test Transaction",
        "recipient": "Test Recipient",
        "sender": "Test Sender",
        "amount": 1000,
        "type": "DEBIT",  # Using string instead of enum
        "transaction_date": datetime.now(timezone.utc).isoformat(),  # Convert to ISO format string
        "meta_data": {"test_key": "test_value"},
        "user_id": test_user.id
    }

@pytest.fixture(scope="function")
def test_transaction(db_session, test_transaction_data):
    from db.models.transaction import Transaction
    transaction = Transaction(**test_transaction_data)
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction