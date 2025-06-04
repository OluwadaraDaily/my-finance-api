from db.models.api_key import APIKey

def test_generate_key():
    raw_key, hashed_key = APIKey.generate_key()
    assert raw_key is not None
    assert hashed_key is not None
    assert raw_key != hashed_key
    assert len(raw_key) == 43
    assert len(hashed_key) == 64

def test_verify_key(test_active_api_key):
    raw_key, api_key = test_active_api_key
    assert APIKey.verify_key(raw_key, api_key.key) is True
    fake_raw_key = "fake_raw_key"
    assert APIKey.verify_key(fake_raw_key, api_key.key) is False

def test_is_expired(test_active_api_key, test_expired_api_key, test_api_key_with_no_expiration):
    _, api_key = test_active_api_key
    assert api_key.is_expired() is False
    _, api_key = test_expired_api_key
    assert api_key.is_expired() is True
    _, api_key = test_api_key_with_no_expiration
    assert api_key.is_expired() is False

def test_is_revoked(test_revoked_api_key):
    _, api_key = test_revoked_api_key
    assert api_key.is_active is False