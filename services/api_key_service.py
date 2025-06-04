from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from db.models.api_key import APIKey
from fastapi import HTTPException, status

class APIKeyService:
    def __init__(self, db: Session):
        self.db = db

    def create_api_key(
        self,
        user_id: str,
        name: str,
        expires_in_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """
        Create a new API key for a user.
        Returns a tuple of (raw_key, api_key_object)
        """
        raw_key, hashed_key = APIKey.generate_key()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = APIKey(
            user_id=user_id,
            name=name,
            key=hashed_key,
            expires_at=expires_at
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        return raw_key, api_key

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get an API key by its ID"""
        return self.db.query(APIKey).filter(APIKey.id == key_id).first()

    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        return self.db.query(APIKey).filter(APIKey.user_id == user_id).all()
    
    def get_all_active_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all active API keys for a user"""
        return self.db.query(APIKey).filter(
            APIKey.user_id == user_id,
            APIKey.is_active == True
        ).all()

    def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """
        Validate an API key and return the associated APIKey object if valid.
        Also updates the last_used_at timestamp.
        """
        # Find the API key by its hash
        api_key = self.db.query(APIKey).filter(
            APIKey.key == APIKey.verify_key(raw_key, APIKey.key)
        ).first()

        if not api_key:
            return None

        if not api_key.is_active or api_key.is_expired():
            return None

        # Update last used timestamp
        api_key.last_used_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return api_key

    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """
        Revoke an API key. Returns True if successful, False if key not found.
        """
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()

        if not api_key:
            return False

        api_key.is_active = False
        self.db.commit()
        return True

    def regenerate_api_key(self, key_id: str, user_id: str) -> tuple[str, APIKey]:
        """
        Regenerate an API key. Returns a tuple of (raw_key, api_key_object)
        """
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id,
            APIKey.is_active == True
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        raw_key, hashed_key = APIKey.generate_key()
        api_key.key = hashed_key
        api_key.last_used_at = None
        
        self.db.commit()
        self.db.refresh(api_key)
        
        return raw_key, api_key 