from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

class EmailService:
    @staticmethod
    def send_activation_email(email: EmailStr, username: str, activation_token: str) -> None:
        pass
    
    @staticmethod
    def send_password_reset_email(email: EmailStr, username: str, reset_token: str) -> None:
        pass