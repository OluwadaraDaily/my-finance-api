# FastAPI app entry point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import auth_router, users_router, api_keys_router, categories_router, budgets_router, pots_router, transactions_router, accounts_router
from db.session import engine
from db.base import Base
from db.models import *  # This imports all models
from services.email_service import EmailService
from pydantic import EmailStr, BaseModel
from core.deps import get_email_core
from contextlib import asynccontextmanager
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_FILE, override=True)

frontend_url = os.getenv("FRONTEND_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title="My Finance API",
    description="API for managing personal finances",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["api-keys"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(budgets_router, prefix="/api/v1/budgets", tags=["budgets"])
app.include_router(pots_router, prefix="/api/v1/pots", tags=["pots"])
app.include_router(transactions_router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(accounts_router, prefix="/api/v1/accounts", tags=["accounts"])

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