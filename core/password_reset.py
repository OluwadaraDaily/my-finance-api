from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session
from db.models.password_reset_token import PasswordResetToken
from db.models.user import User


class PasswordResetService:
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_reset_token(db: Session, user: User) -> PasswordResetToken:
        """Create a new password reset token for a user"""
        # Delete any existing unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).delete()

        # Create new token with timezone-aware datetime
        current_time = datetime.now(timezone.utc)
        token = PasswordResetToken(
            user_id=user.id,
            token=PasswordResetService.generate_token(),
            expires_at=current_time + timedelta(hours=1)  # Token expires in 1 hour
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def verify_token(db: Session, token: str) -> tuple[bool, str]:
        """Verify a password reset token and return (is_valid, message)"""
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.is_used == False
        ).first()

        if not reset_token:
            return False, "Invalid or already used token"

        # Ensure both datetimes are timezone-aware
        current_time = datetime.now(timezone.utc)
        expires_at = reset_token.expires_at.replace(tzinfo=timezone.utc) if reset_token.expires_at.tzinfo is None else reset_token.expires_at

        if expires_at < current_time:
            return False, "Token has expired"

        return True, "Token is valid"

    @staticmethod
    def get_token(db: Session, token: str) -> PasswordResetToken | None:
        """Get a password reset token by token string"""
        return db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()

    @staticmethod
    def mark_token_used(db: Session, token: PasswordResetToken) -> None:
        """Mark a token as used"""
        token.is_used = True
        db.commit()
