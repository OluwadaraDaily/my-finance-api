from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.session import get_db
from services.api_key_service import APIKeyService
from core.deps import get_current_user, get_api_key_user
from db.models.user import User
from schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, GetAPIKeyResponse

router = APIRouter()

@router.post("/", response_model=APIKeyCreateResponse)
async def create_api_key(
    request: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user"""
    api_key_service = APIKeyService(db)
    raw_key, api_key = api_key_service.create_api_key(
        user_id=current_user.id,
        name=request.name,
        expires_in_days=request.expires_in_days
    )
    
    return {
        "data": {
          "api_key": APIKeyResponse(
            id=api_key.id,
            name=api_key.name,
            created_at=api_key.created_at,
            key=api_key.key,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            is_active=api_key.is_active
            ),
            "raw_key": raw_key
        },
        "message": "API key created successfully"
    }

@router.get("/", response_model=GetAPIKeyResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user"""
    api_key_service = APIKeyService(db)
    api_keys = api_key_service.get_user_api_keys(current_user.id)
    
    return {
      "data": [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key=key.key,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            is_active=key.is_active
        )
        for key in api_keys
      ],
      "message": "API keys fetched successfully"
    }

@router.get("/active", response_model=GetAPIKeyResponse)
async def list_active_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active API keys for the current user"""
    api_key_service = APIKeyService(db)
    api_keys = api_key_service.get_all_active_api_keys(current_user.id)
    
    return {
      "data": [
        APIKeyResponse(
          id=key.id,
          name=key.name,
          key=key.key,
          created_at=key.created_at,
          last_used_at=key.last_used_at,
          expires_at=key.expires_at,
          is_active=key.is_active
        )
        for key in api_keys
      ],
      "message": "Active API keys fetched successfully"
    }

@router.delete("/{key_id}", response_model=dict)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key"""
    api_key_service = APIKeyService(db)
    if not api_key_service.revoke_api_key(key_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return {"message": "API key revoked successfully"}

@router.post("/{key_id}/regenerate", response_model=APIKeyCreateResponse)
async def regenerate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate an API key"""
    api_key_service = APIKeyService(db)
    try:
        raw_key, api_key = api_key_service.regenerate_api_key(key_id, current_user.id)
        return {
            "data": {
              "api_key": APIKeyResponse(
                id=api_key.id,
                name=api_key.name,
                key=api_key.key,
                created_at=api_key.created_at,
                last_used_at=api_key.last_used_at,
                expires_at=api_key.expires_at,
                is_active=api_key.is_active
                ),
                "raw_key": raw_key
            },
            "message": "API key regenerated successfully"
        }
    except HTTPException as error:
        raise error 
    

@router.get("/test", response_model=dict)
async def test_api_key(
    current_user: User = Depends(get_api_key_user)
):
    """Test an API key"""
    return {
        "data": {
            "message": "API key is valid",
            "user": {
                "email": current_user.email,
                "id": str(current_user.id)
            }
        }
    }