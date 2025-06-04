from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Generator, Optional

from db.session import get_db
from db.models.user_auth import UserAuth
from db.models.user import User
from db.models.api_key import APIKey
from services.api_key_service import APIKeyService
from core.config import settings
from core.jwt import verify_token
from core.email import EmailCore

security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        token = credentials.credentials
        try:
            payload = verify_token(token)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired or is invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Verify token is still active in database
        user_auth = db.query(UserAuth).filter(
            UserAuth.access_token == token,
            UserAuth.is_active == True
        ).first()
        
        if not user_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated"
            )
        
        return user_auth.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_api_key_user(
    api_key: str,
    db: Session = Depends(get_db)
) -> User:
    """
    Validate API key and return the associated user.
    To be used as a dependency in protected endpoints.
    """
    api_key_service = APIKeyService(db)
    api_key_obj = api_key_service.validate_api_key(api_key)
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    user = db.query(User).filter(User.id == api_key_obj.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

def get_email_core() -> EmailCore:
    """
    Get email core instance.
    """
    return EmailCore() 