# Pydantic settings
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path
import os
from dotenv import load_dotenv

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Load .env file
load_dotenv(ENV_FILE, override=True)

class Settings(BaseSettings):
    # Database settings
    DB_URL: str

    # Email settings
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "My Finance"
    RESEND_API_KEY: str

    JWT_SECRET_KEY: str

    # Test database settings
    TEST_DB_URL: str

    # Activation settings (set to False in production to skip email activation)
    REQUIRE_ACTIVATION: bool = True

    # Environment settings
    DEBUG: bool = True
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = ConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

# Initialize settings
settings = Settings(
    _env_file=ENV_FILE,
    _env_file_encoding='utf-8',
    _env_nested_delimiter='__'
)