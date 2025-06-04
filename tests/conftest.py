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
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["JWT_SECRET_KEY"] = TEST_JWT_SECRET
    yield
    # Clean up if needed
    if "JWT_SECRET_KEY" in os.environ:
        del os.environ["JWT_SECRET_KEY"]

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
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
    db_session.refresh(user)  # Ensure user is attached to session
    
    yield user  # Use yield instead of return
    
    # Cleanup
    db_session.rollback()  # Rollback any pending changes
    if user in db_session:
        db_session.refresh(user)  # Refresh before using in cleanup

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
def test_invalid_api_key(db_session, test_user):
    from services.api_key_service import APIKeyService
    api_key_service = APIKeyService(db_session)
    raw_key, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    api_key.is_active = False
    db_session.commit()
    return raw_key, api_key

@pytest.fixture(scope="function")
def test_inactive_api_key(db_session, test_user):
    from services.api_key_service import APIKeyService
    api_key_service = APIKeyService(db_session)
    raw_key, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    api_key.is_active = False
    db_session.commit()
    return raw_key, api_key