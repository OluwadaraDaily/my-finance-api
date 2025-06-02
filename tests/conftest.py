import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from db.base import Base
from db.session import get_db
from core.config import settings
from core.security import get_password_hash

# Test database URL
DATABASE_URL = settings.TEST_DB_URL

# Create test engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Ensures connection is still valid before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    return user 