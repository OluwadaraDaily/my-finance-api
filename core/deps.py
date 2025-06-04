from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Generator, Optional
import os

from db.session import get_db
from db.models.user_auth import UserAuth
from db.models.user import User
from db.models.api_key import APIKey
from services.api_key_service import APIKeyService
from core.config import settings
from core.jwt import verify_token
from core.email import EmailCore
from crud.user import UserCRUD

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Use test secret key if in test environment
        secret_key = os.getenv("JWT_SECRET_KEY")
        payload = verify_token(token, secret_key=secret_key)
        
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = UserCRUD(db).get_by_email(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_api_key_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Validate API key and return the associated user.
    To be used as a dependency in protected endpoints.
    """
    # Get API key from header 'X-API-Key'
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
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
    
    # Refresh user to ensure it's bound to the session
    db.refresh(user)
    return user

def get_email_core() -> EmailCore:
    """
    Get email core instance.
    """
    return EmailCore() 