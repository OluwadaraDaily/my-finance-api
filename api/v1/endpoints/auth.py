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

    Args:
        user: UserCreate object containing user details
        db: Database session
        email_service: Email service instance

    Returns:
        {
            "message": "User registered successfully. Please check your email to activate your account.",
            "data": UserSchema
        }
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate activation token
    activation_token = ActivationService.create_activation_token(db, db_user)
    
    # Send activation email
    await email_service.send_activation_email(
        email=db_user.email,
        username=db_user.username,
        activation_token=activation_token.token
    )
    
    return {
        "message": "User registered successfully. Please check your email to activate your account.",
        "data": UserSchema.model_validate(db_user)
    }

@router.post("/auth/login", response_model=dict)
async def login(user: UserLogin, db: Session = Depends(get_db)) -> dict:
    """
    Login a user.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    
    # Store tokens in database
    user_auth = UserAuth(
        user_id=db_user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        is_active=True,
        is_expired=False
    )
    db.add(user_auth)
    db.commit()
    
    return {
        "message": "Login successful",
        "data": {
            "user": UserSchema.model_validate(db_user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    }

@router.get("/auth/activate/{token}", response_model=dict)
async def activate_account(token: str, db: Session = Depends(get_db)) -> dict:
    """
    Activate a user account using the activation token.
    """
    is_valid, message = ActivationService.verify_token(db, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    activation_token = db.query(ActivationToken).filter(
        ActivationToken.token == token
    ).first()
    
    # Activate the user
    user = activation_token.user
    user.is_activated = True
    
    # Mark token as used
    activation_token.is_used = True
    
    db.commit()
    
    return {
        "message": "Account activated successfully",
        "data": UserSchema.model_validate(user)
    }

@router.post("/auth/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> dict:
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        db_user = crud.get_user_by_email(db, email=email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get existing auth record
        user_auth = db.query(UserAuth).filter(
            UserAuth.user_id == db_user.id,
            UserAuth.refresh_token == request.refresh_token,
            UserAuth.is_active == True
        ).first()
        
        if not user_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        new_access_token = create_access_token(
            data={"sub": db_user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        new_refresh_token = create_refresh_token(data={"sub": db_user.email})
        
        # Update tokens in database
        user_auth.access_token = new_access_token
        user_auth.refresh_token = new_refresh_token
        db.commit()
        
        return {
            "message": "Tokens refreshed successfully",
            "data": {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/auth/logout")
async def logout(request: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    """
    Logout user by invalidating tokens.
    """
    try:
        # Verify access token
        payload = verify_token(request.access_token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )
        
        # Get user from database
        db_user = crud.get_user_by_email(db, email=email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Invalidate tokens
        user_auth = db.query(UserAuth).filter(
            UserAuth.user_id == db_user.id,
            UserAuth.access_token == request.access_token,
            UserAuth.is_active == True
        ).first()
        
        if user_auth:
            user_auth.is_active = False
            user_auth.is_expired = True
            db.commit()
        
        return {
            "message": "Successfully logged out"
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )

