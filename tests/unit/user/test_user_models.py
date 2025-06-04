import pytest
from sqlalchemy.exc import IntegrityError
from db.models.user import User

def test_create_user(db_session):
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"

def test_user_email_unique(db_session):
    # Create first user
    user1 = User(
        email="test@example.com",
        username="testuser1",
        hashed_password="hashed_password"
    )
    db_session.add(user1)
    db_session.commit()
    
    # Try to create second user with same email
    user2 = User(
        email="test@example.com",
        username="testuser2",
        hashed_password="hashed_password"
    )
    db_session.add(user2)
    
    with pytest.raises(IntegrityError):
        db_session.commit() 