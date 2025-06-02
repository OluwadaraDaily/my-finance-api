# Pydantic settings
from pydantic_settings import BaseSettings
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
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "My Finance"

    JWT_SECRET_KEY: str

    # Test database settings
    TEST_DB_URL: str

    class Config:
        env_file = ENV_FILE
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'ignore'

# Initialize settings
settings = Settings(
    _env_file=ENV_FILE,
    _env_file_encoding='utf-8',
    _env_nested_delimiter='__'
)