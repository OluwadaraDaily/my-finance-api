from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from schemas.user import UserCreate, User as UserSchema, UserLogin
from db.models.user_auth import UserAuth
from core.security import get_password_hash, verify_password
from core.jwt import create_access_token, create_refresh_token, verify_token
from services.email_service import EmailService
from core.activation import ActivationService
from core.password_reset import PasswordResetService
from db.models.password_reset_token import PasswordResetToken
from crud.user import UserCRUD
from core.jwt import ACCESS_TOKEN_EXPIRE_MINUTES
from jose import JWTError
from db.models.activation_token import ActivationToken
from services.account_service import AccountService
from core.config import settings
import os

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_crud = UserCRUD(db)

    async def register_user(self, user: UserCreate, email_service: EmailService) -> dict:
        """
        Register a new user and send activation email.

        Args:
            user: UserCreate object containing user details
            email_service: Email service instance for sending activation email

        Returns:
            dict: Contains success message and user data
        """
        # Check if user exists
        if self.user_crud.get_by_email(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        user_data = user.model_dump()
        user_data["password"] = get_password_hash(user.password)
        
        # Create user
        db_user = self.user_crud.create(UserCreate(**user_data))

        # Check if activation is required (can be disabled in production)
        if settings.REQUIRE_ACTIVATION:
            # Generate activation token and send email
            activation_token = ActivationService.create_activation_token(self.db, db_user)
            await email_service.send_activation_email(
                email=db_user.email,
                username=db_user.username,
                activation_token=activation_token.token
            )

            return {
                "message": "User registered successfully. Please check your email to activate your account.",
                "data": UserSchema.model_validate(db_user)
            }
        else:
            # Auto-activate user and create account (no email verification)
            db_user.is_activated = True
            account_service = AccountService(self.db)
            account = account_service.get_or_create_account(db_user.id)
            db_user.account_id = account.id
            self.db.commit()
            self.db.refresh(db_user)

            return {
                "message": "User registered successfully.",
                "data": UserSchema.model_validate(db_user)
            }

    async def login_user(self, user: UserLogin) -> dict:
        """
        Authenticate a user and generate access and refresh tokens.

        Args:
            user: UserLogin object containing email and password

        Returns:
            dict: Contains user data and authentication tokens
        """
        db_user = self.user_crud.get_by_email(email=user.email)
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
        
        # Use test secret key if in test environment
        secret_key = os.getenv("JWT_SECRET_KEY")

        # Invalidate all existing and active tokens for the user
        self.db.query(UserAuth).filter(
            UserAuth.user_id == db_user.id,
            UserAuth.is_active == True
        ).update({
            "is_active": False,
            "is_expired": True
        })
        self.db.commit()
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": db_user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            secret_key=secret_key
        )
        refresh_token = create_refresh_token(
            data={"sub": db_user.email},
            secret_key=secret_key
        )
        
        # Store tokens in database
        user_auth = UserAuth(
            user_id=db_user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            is_active=True,
            is_expired=False
        )
        self.db.add(user_auth)
        self.db.commit()
        
        return {
            "message": "Login successful",
            "data": {
                "user": UserSchema.model_validate(db_user),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.
        Implements token rotation - each refresh token can only be used once.
        
        Args:
            refresh_token: The refresh token to use

        Returns:
            dict: Contains new access and refresh tokens
        """
        try:
            # Verify refresh token
            payload = verify_token(refresh_token)
            email = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Get user from database
            db_user = self.user_crud.get_by_email(email=email)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get existing auth record and validate refresh token
            user_auth = self.db.query(UserAuth).filter(
                UserAuth.user_id == db_user.id,
                UserAuth.refresh_token == refresh_token,
                UserAuth.is_active == True,
                UserAuth.is_expired == False
            ).first()
            
            if not user_auth:
                # Potential reuse of refresh token - invalidate all tokens for security
                self.db.query(UserAuth).filter(
                    UserAuth.user_id == db_user.id,
                    UserAuth.is_active == True
                ).update({
                    "is_active": False,
                    "is_expired": True
                })
                self.db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been invalidated"
                )
            
            # Generate new tokens
            new_access_token = create_access_token(
                data={"sub": db_user.email},
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            new_refresh_token = create_refresh_token(data={"sub": db_user.email})
            
            # Invalidate old refresh token
            user_auth.is_active = False
            user_auth.is_expired = True
            
            # Create new auth record with new tokens
            new_user_auth = UserAuth(
                user_id=db_user.id,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                is_active=True,
                is_expired=False
            )
            self.db.add(new_user_auth)
            self.db.commit()
            
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
                detail="Invalid or expired refresh token"
            )

    async def logout(self, access_token: str) -> dict:
        """
        Logout user by invalidating tokens.

        Args:
            access_token: The access token to invalidate

        Returns:
            dict: Success message
        """
        try:
            # Verify access token
            payload = verify_token(access_token)
            email = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )
            
            # Get user from database
            db_user = self.user_crud.get_by_email(email=email)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Invalidate tokens
            user_auth = self.db.query(UserAuth).filter(
                UserAuth.user_id == db_user.id,
                UserAuth.access_token == access_token,
                UserAuth.is_active == True
            ).first()
            
            if user_auth:
                user_auth.is_active = False
                user_auth.is_expired = True
                self.db.commit()
            
            return {
                "message": "Successfully logged out"
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )

    async def activate_account(self, token: str) -> dict:
        """
        Activate a user account using the activation token.

        Args:
            token: The activation token

        Returns:
            dict: Contains success message and user data
        """
        is_valid, message = ActivationService.verify_token(self.db, token)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        activation_token = self.db.query(ActivationToken).filter(
            ActivationToken.token == token
        ).first()
        
        # Activate the user
        user = activation_token.user
        user.is_activated = True
        
        # Mark token as used
        activation_token.is_used = True
        
        # Create an account for the user
        account_service = AccountService(self.db)
        account = account_service.get_or_create_account(user.id)

        # Update user with account_id
        user.account_id = account.id
        
        self.db.commit()
        self.db.refresh(user)
        
        return {
            "message": "Account activated successfully",
            "data": {
                "user": UserSchema.model_validate(user),
                "account": account
            }
        } 
    
    async def validate_token(self, access_token: str) -> dict:
        """
        Validate a token.
        """
        try:
            payload = verify_token(access_token)
            email = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )

            return {
                "message": "Token validated successfully"
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )

    async def resend_activation_email(self, email: str, email_service: EmailService) -> dict:
        """
        Resend activation email to a user.

        Args:
            email: The user's email address
            email_service: Email service instance for sending activation email

        Returns:
            dict: Success message
        """
        db_user = self.user_crud.get_by_email(email=email)
        if not db_user:
            # Return success even if user not found to prevent email enumeration
            return {
                "message": "If an account exists with this email, an activation link has been sent."
            }

        if db_user.is_activated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is already activated"
            )

        # Generate new activation token and send email
        activation_token = ActivationService.create_activation_token(self.db, db_user)
        await email_service.send_activation_email(
            email=db_user.email,
            username=db_user.username,
            activation_token=activation_token.token
        )

        return {
            "message": "If an account exists with this email, an activation link has been sent."
        }

    async def forgot_password(self, email: str, email_service: EmailService) -> dict:
        """
        Send password reset email to a user.

        Args:
            email: The user's email address
            email_service: Email service instance for sending password reset email

        Returns:
            dict: Success message
        """
        db_user = self.user_crud.get_by_email(email=email)
        if not db_user:
            # Return success even if user not found to prevent email enumeration
            return {
                "message": "If an account exists with this email, a password reset link has been sent."
            }

        # Generate password reset token and send email
        reset_token = PasswordResetService.create_reset_token(self.db, db_user)
        await email_service.send_password_reset_email(
            email=db_user.email,
            username=db_user.username,
            reset_token=reset_token.token
        )

        return {
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    async def validate_reset_token(self, token: str) -> dict:
        """
        Validate a password reset token.

        Args:
            token: The password reset token

        Returns:
            dict: Success message if token is valid
        """
        is_valid, message = PasswordResetService.verify_token(self.db, token)
        if not is_valid:
            status_code = status.HTTP_410_GONE if "expired" in message.lower() else status.HTTP_400_BAD_REQUEST
            raise HTTPException(
                status_code=status_code,
                detail=message
            )

        return {
            "message": "Token is valid"
        }

    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Reset a user's password using a reset token.

        Args:
            token: The password reset token
            new_password: The new password

        Returns:
            dict: Success message
        """
        is_valid, message = PasswordResetService.verify_token(self.db, token)
        if not is_valid:
            status_code = status.HTTP_410_GONE if "expired" in message.lower() else status.HTTP_400_BAD_REQUEST
            raise HTTPException(
                status_code=status_code,
                detail=message
            )

        reset_token = PasswordResetService.get_token(self.db, token)
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )

        # Update user's password
        user = reset_token.user
        user.hashed_password = get_password_hash(new_password)

        # Mark token as used
        PasswordResetService.mark_token_used(self.db, reset_token)

        # Invalidate all existing auth tokens for security
        self.db.query(UserAuth).filter(
            UserAuth.user_id == user.id,
            UserAuth.is_active == True
        ).update({
            "is_active": False,
            "is_expired": True
        })

        self.db.commit()

        return {
            "message": "Password reset successfully"
        }