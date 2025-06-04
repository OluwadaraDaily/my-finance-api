from datetime import datetime, timezone, timedelta
from services.api_key_service import APIKeyService
import pytest

def test_create_api_key(db_session, test_user):
    api_key_service = APIKeyService(db_session)
    raw_key_1, api_key_1 = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    assert raw_key_1 is not None
    assert api_key_1 is not None
    assert api_key_1.user_id == test_user.id
    assert api_key_1.name == "Test API Key"
    assert api_key_1.expires_at is not None
    assert api_key_1.is_active is True

    _, api_key_2 = api_key_service.create_api_key(test_user.id, "Test API Key", None)
    assert api_key_2.expires_at is None

    # Verify database persistence
    db_session.refresh(api_key_1)
    assert api_key_1.expires_at is not None
    assert api_key_1.is_active is True

    # Verify expiration date is set correctly
    expires_at = api_key_1.expires_at.replace(tzinfo=timezone.utc) if api_key_1.expires_at.tzinfo is None else api_key_1.expires_at
    now = datetime.now(timezone.utc)
    assert expires_at > now

def test_validate_api_key(db_session, test_active_api_key, test_invalid_api_key, test_expired_api_key, test_inactive_api_key):
    api_key_service = APIKeyService(db_session)
    raw_key_1, api_key_1 = test_active_api_key
    raw_key_2, _ = test_invalid_api_key
    raw_key_3, _ = test_expired_api_key
    raw_key_4, _ = test_inactive_api_key

    # Refresh the active key from database to ensure latest state
    db_session.refresh(api_key_1)
    validated_key = api_key_service.validate_api_key(raw_key_1)
    assert validated_key is not None
    assert validated_key.id == api_key_1.id

    assert api_key_service.validate_api_key(raw_key_2) is None
    assert api_key_service.validate_api_key(raw_key_3) is None
    assert api_key_service.validate_api_key(raw_key_4) is None

    # Verify expiration date with proper timezone handling
    validated_key = api_key_service.validate_api_key(raw_key_1)
    assert validated_key.expires_at is not None
    expires_at = validated_key.expires_at.replace(tzinfo=timezone.utc) if validated_key.expires_at.tzinfo is None else validated_key.expires_at
    now = datetime.now(timezone.utc)
    assert expires_at > now

def test_get_user_api_keys(db_session, test_user):
    api_key_service = APIKeyService(db_session)
    
    assert api_key_service.get_user_api_keys(test_user.id) == []

    _, api_key_1 = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    _, api_key_2 = api_key_service.create_api_key(test_user.id, "Test API Key 2", 30)
    _, api_key_3 = api_key_service.create_api_key(test_user.id, "Test API Key 3", 30)

    assert api_key_1 in api_key_service.get_user_api_keys(test_user.id)
    assert api_key_2 in api_key_service.get_user_api_keys(test_user.id)
    assert api_key_3 in api_key_service.get_user_api_keys(test_user.id)

def test_get_all_active_api_keys(db_session, test_user):
    api_key_service = APIKeyService(db_session)
    
    _, api_key_1 = api_key_service.create_api_key(test_user.id, "Test API Key", 30)
    _, api_key_2 = api_key_service.create_api_key(test_user.id, "Test API Key 2", 30)
    _, api_key_3 = api_key_service.create_api_key(test_user.id, "Test API Key 3", 30)

    assert api_key_1 in api_key_service.get_all_active_api_keys(test_user.id)
    assert api_key_2 in api_key_service.get_all_active_api_keys(test_user.id)
    assert api_key_3 in api_key_service.get_all_active_api_keys(test_user.id)

    api_key_1.is_active = False
    db_session.commit()
    db_session.refresh(api_key_1)
    
    active_keys = api_key_service.get_all_active_api_keys(test_user.id)
    assert api_key_1 not in active_keys

def test_revoke_api_key(db_session, test_user, test_active_api_key):
    api_key_service = APIKeyService(db_session)
    _, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", 30)

    assert api_key.is_active is True
    
    assert api_key_service.revoke_api_key(api_key.id, test_user.id) is True
    db_session.refresh(api_key)
    assert api_key.is_active is False
    
    assert api_key_service.revoke_api_key(api_key.id, test_user.id) is False
    
    _, active_api_key = test_active_api_key
    assert api_key_service.revoke_api_key(active_api_key.id, test_user.id) is True

def test_regenerate_api_key(db_session, test_user, test_active_api_key):
    api_key_service = APIKeyService(db_session)
    _, api_key = api_key_service.create_api_key(test_user.id, "Test API Key", 30)

    assert api_key.is_active is True
    old_key = api_key.key  # Store the old key

    _, regenerated_key = api_key_service.regenerate_api_key(api_key.id, test_user.id)
    db_session.refresh(api_key)  # Refresh to get the latest state
    assert regenerated_key is not None
    assert regenerated_key.is_active is True
    assert regenerated_key.key != old_key