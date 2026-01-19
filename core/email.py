from pydantic import EmailStr
from typing import Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import resend
import os


resend.api_key = os.getenv("RESEND_API_KEY")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
MAIL_FROM = os.getenv("MAIL_FROM")

class EmailCore:
    def __init__(self):
        self.template_folder = Path(__file__).parent.parent / 'templates'
        self.template_env = Environment(
            loader=FileSystemLoader(self.template_folder)
        )

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

            params: resend.Emails.SendParams = {
                "from": f"{MAIL_FROM_NAME} <{MAIL_FROM}>",
                "to": [to],
                "subject": subject,
                "html": html_content,
            }
            email: resend.Emails.SendResponse = resend.Emails.send(params)
            return email
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