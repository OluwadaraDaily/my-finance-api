from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Generator, Optional
import os
import logging

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
    logger = logging.getLogger(__name__)
    try:
        # Extract token from credentials
        token = credentials.credentials
        logger.info("Received token from credentials")
        
        # Use test secret key if in test environment
        secret_key = os.getenv("JWT_SECRET_KEY")
        logger.info(f"Using JWT secret key: {'[MASKED]' if secret_key else 'None'}")
        
        try:
            payload = verify_token(token, secret_key=secret_key)
            logger.info(f"Token verification successful. Payload: {payload}")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not payload or "sub" not in payload:
            logger.error(f"Invalid payload structure: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials - missing subject"
            )
            
        logger.info(f"Looking up user with email: {payload['sub']}")
        
        # Create a new UserCRUD instance with the current session
        user_crud = UserCRUD(db)
        user = user_crud.get_by_email(payload["sub"])
        
        logger.info(f"User lookup result: {user}")
        
        if not user:
            logger.error(f"No user found for email: {payload['sub']}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token has expired or is invalid: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
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