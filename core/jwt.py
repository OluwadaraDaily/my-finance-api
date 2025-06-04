from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_FILE, override=True)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    key_to_use = secret_key or SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key_to_use, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    data: dict,
    secret_key: Optional[str] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    key_to_use = secret_key or SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key_to_use, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(
    token: str,
    secret_key: Optional[str] = None
) -> dict:
    try:
        key_to_use = secret_key or SECRET_KEY
        payload = jwt.decode(token, key_to_use, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        ) 