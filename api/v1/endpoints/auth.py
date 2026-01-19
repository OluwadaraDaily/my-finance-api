# Authentication endpoints
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.user import UserCreate, UserLogin
from services.email_service import EmailService
from services.auth_service import AuthService
from core.deps import get_email_core
from schemas.auth import RefreshTokenRequest, LogoutRequest, EmailRequest, ResetPasswordRequest

router = APIRouter()

@router.post("/register", response_model=dict)
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

@router.post("/login", response_model=dict)
async def login(user: UserLogin, db: Session = Depends(get_db)) -> dict:
    """
    Login a user.
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(user)

@router.get("/activate/{token}", response_model=dict)
async def activate_account(token: str, db: Session = Depends(get_db)) -> dict:
    """
    Activate a user account using the activation token.
    """
    auth_service = AuthService(db)
    return await auth_service.activate_account(token)

@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> dict:
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_token(request.refresh_token)

@router.post("/logout")
async def logout(request: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    """
    Logout user by invalidating tokens.
    """
    auth_service = AuthService(db)
    return await auth_service.logout(request.access_token)

@router.post("/validate-token")
async def validate_token(request: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    """
    Validate a token.
    """
    auth_service = AuthService(db)
    return await auth_service.validate_token(request.access_token)


@router.post("/resend-activation", response_model=dict)
async def resend_activation(
    request: EmailRequest,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(lambda: EmailService(get_email_core()))
) -> dict:
    """
    Resend activation email to a user.
    """
    auth_service = AuthService(db)
    return await auth_service.resend_activation_email(request.email, email_service)


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    request: EmailRequest,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(lambda: EmailService(get_email_core()))
) -> dict:
    """
    Send password reset email to a user.
    """
    auth_service = AuthService(db)
    return await auth_service.forgot_password(request.email, email_service)


@router.get("/validate-reset-token/{token}", response_model=dict)
async def validate_reset_token(token: str, db: Session = Depends(get_db)) -> dict:
    """
    Validate a password reset token.
    """
    auth_service = AuthService(db)
    return await auth_service.validate_reset_token(token)


@router.post("/reset-password/{token}", response_model=dict)
async def reset_password(
    token: str,
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Reset a user's password using a reset token.
    """
    auth_service = AuthService(db)
    return await auth_service.reset_password(token, request.new_password)
