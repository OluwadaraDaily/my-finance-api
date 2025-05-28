from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Optional
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from core.config import settings
import ssl
from fastapi import HTTPException

class EmailCore:
    def __init__(self):
        self.configuration = ConnectionConfig(
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
        
        self.template_env = Environment(
            loader=FileSystemLoader(self.configuration.TEMPLATE_FOLDER)
        )
        self.fastmail = FastMail(self.configuration)

    async def send_email(
        self,
        to: EmailStr,
        subject: str,
        html_content: str,
        template_name: Optional[str] = None,
        template_data: Optional[dict] = None
    ) -> None:
        """
        Core method to send emails with optional template rendering.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML content (if template_name is not provided)
            template_name: Optional template name to render
            template_data: Optional data for template rendering
        """
        try:
            if template_name and template_data:
                html_content = self.render_template(template_name, **template_data)

            message = MessageSchema(
                subject=subject,
                recipients=[to],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {str(e)}"
            )

    def render_template(self, template_name: str, **kwargs) -> str:
        """
        Render a template with the given data.
        
        Args:
            template_name: Name of the template file
            **kwargs: Data to render in the template
            
        Returns:
            Rendered template as string
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to render template: {str(e)}"
            )