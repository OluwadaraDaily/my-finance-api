from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..base import Base
import secrets
import hashlib

class  APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)  # For identifying different API keys (e.g., "Telegram Bot")
    key = Column(String(255), nullable=False, unique=True)  # The hashed API key
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key() -> tuple[str, str]:
        """
        Generate a new API key and its hash.
        Returns a tuple of (raw_key, hashed_key)
        """
        raw_key = secrets.token_urlsafe(32)
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, hashed_key

    @staticmethod
    def verify_key(raw_key: str, hashed_key: str) -> bool:
        """
        Verify if a raw API key matches its hash.
        """
        return hashlib.sha256(raw_key.encode()).hexdigest() == hashed_key

    def is_expired(self) -> bool:
        """
        Check if the API key has expired.
        """
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at 