# Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.session import get_db
from db.models.user import User
from core.security import get_password_hash, verify_password
from crud import user as crud
from schemas.user import UserCreate, User as UserSchema
from core.activation import ActivationService
from core.email import EmailService
from db.models.activation_token import ActivationToken

router = APIRouter()

@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate, db: Session = Depends(get_db)) -> dict:
    """
    Register a new user and send activation email.

    Args:
        user: UserCreate object containing user details
        db: Database session

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
    await EmailService.send_activation_email(
        email=db_user.email,
        username=db_user.username,
        activation_token=activation_token.token
    )
    
    return {
        "message": "User registered successfully. Please check your email to activate your account.",
        "data": UserSchema.model_validate(db_user)
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