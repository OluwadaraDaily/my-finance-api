# FastAPI app entry point

from fastapi import FastAPI
from api.v1.endpoints import auth_router, users_router
from db.session import engine
from db.base import Base
from db.models import *  # This imports all models
from services.email_service import EmailService
from pydantic import EmailStr, BaseModel
from core.deps import get_email_core

app = FastAPI()

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

class EmailRequest(BaseModel):
    email: EmailStr

@app.post("/test-email")
async def test_email(request: EmailRequest):
    """Test endpoint to verify email configuration"""
    try:
        await EmailService(get_email_core()).send_activation_email(
            email=request.email,
            username="Test User",
            activation_token="test-token"
        )
        return {"message": "Test email sent successfully!"}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}