from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from core.config import settings
import ssl

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates'
)

# Initialize Jinja2 environment
template_env = Environment(
    loader=FileSystemLoader(conf.TEMPLATE_FOLDER)
)

class EmailService:
    @staticmethod
    async def send_activation_email(email: EmailStr, username: str, activation_token: str) -> None:
        """Send account activation email to user."""
        try:
            template = template_env.get_template('activation_email.html')
            html_content = template.render(
                username=username,
                activation_token=activation_token
            )
            
            message = MessageSchema(
                subject="Activate Your Account",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as e:
            raise
    
    @staticmethod
    async def send_password_reset_email(email: EmailStr, username: str, reset_token: str) -> None:
        """Send password reset email to user."""
        try:
            template = template_env.get_template('password_reset_email.html')
            html_content = template.render(
                username=username,
                reset_token=reset_token
            )
            
            message = MessageSchema(
                subject="Password Reset Request",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as e:
            raise