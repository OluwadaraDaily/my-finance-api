from fastapi import APIRouter
from db.models.user import User
from fastapi import Depends
from core.deps import get_current_user

router = APIRouter()

@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user
