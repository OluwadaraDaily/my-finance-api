# Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.session import get_db
from db.models.user import User
from core.security import get_password_hash, verify_password
from crud import user as crud
from schemas.user import UserCreate, UserLogin, User as UserSchema
from core.activation import ActivationService
from services.email_service import EmailService
from services.auth_service import AuthService
from core.deps import get_email_core
from db.models.activation_token import ActivationToken
from core.jwt import create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES, verify_token
from datetime import timedelta
from db.models.user_auth import UserAuth
from jose import JWTError
from schemas.auth import RefreshTokenRequest, LogoutRequest

router = APIRouter()

@router.post("/auth/register", response_model=dict)
async def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(lambda: EmailService(get_email_core()))
) -> dict:
    """
    Register a new user and send activation email.
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(user, email_service)

@router.post("/auth/login", response_model=dict)
async def login(user: UserLogin, db: Session = Depends(get_db)) -> dict:
    """
    Login a user.
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(user)

@router.get("/auth/activate/{token}", response_model=dict)
async def activate_account(token: str, db: Session = Depends(get_db)) -> dict:
    """
    Activate a user account using the activation token.
    """
    auth_service = AuthService(db)
    return await auth_service.activate_account(token)

@router.post("/auth/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> dict:
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_token(request.refresh_token)

@router.post("/auth/logout")
async def logout(request: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    """
    Logout user by invalidating tokens.
    """
    auth_service = AuthService(db)
    return await auth_service.logout(request.access_token)

