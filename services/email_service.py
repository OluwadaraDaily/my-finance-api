from pydantic import EmailStr
from core.email import EmailCore
from fastapi import HTTPException

class EmailService:
    def __init__(self, email_core: EmailCore):
        self.email_core = email_core

    async def send_activation_email(self, email: EmailStr, username: str, activation_token: str) -> None:
        """
        Send account activation email to user.
        
        Args:
            email: Recipient email address
            username: User's username
            activation_token: Token for account activation
        """
        try:
            await self.email_core.send_email(
                to=email,
                subject="Activate Your Account",
                html_content="",  # Will be rendered from template
                template_name="activation_email.html",
                template_data={
                    "username": username,
                    "activation_token": activation_token
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send activation email: {str(e)}"
            )

    async def send_password_reset_email(self, email: EmailStr, username: str, reset_token: str) -> None:
        """
        Send password reset email to user.
        
        Args:
            email: Recipient email address
            username: User's username
            reset_token: Token for password reset
        """
        try:
            await self.email_core.send_email(
                to=email,
                subject="Password Reset Request",
                html_content="",  # Will be rendered from template
                template_name="password_reset_email.html",
                template_data={
                    "username": username,
                    "reset_token": reset_token
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send password reset email: {str(e)}"
            )