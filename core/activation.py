from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session
from db.models.activation_token import ActivationToken
from db.models.user import User

class ActivationService:
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_activation_token(db: Session, user: User) -> ActivationToken:
        """Create a new activation token for a user"""
        # Delete any existing unused tokens
        db.query(ActivationToken).filter(
            ActivationToken.user_id == user.id,
            ActivationToken.is_used == False
        ).delete()
        
        # Create new token
        token = ActivationToken(
            user_id=user.id,
            token=ActivationService.generate_token(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)  # Token expires in 24 hours
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token
    
    @staticmethod
    def verify_token(db: Session, token: str) -> tuple[bool, str]:
        """Verify an activation token and return (is_valid, message)"""
        activation_token = db.query(ActivationToken).filter(
            ActivationToken.token == token,
            ActivationToken.is_used == False
        ).first()
        
        if not activation_token:
            return False, "Invalid or already used token"
            
        if activation_token.expires_at < datetime.now(timezone.utc):
            return False, "Token has expired"
            
        return True, "Token is valid" 