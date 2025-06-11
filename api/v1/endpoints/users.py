from fastapi import APIRouter
from fastapi import Depends
from core.deps import get_current_user
from schemas.common import ResponseModel
from schemas.user import User as UserSchema
from db.models.user import User as UserModel

router = APIRouter()

@router.get("/me", response_model=ResponseModel[UserSchema])
async def get_current_user(current_user: UserModel = Depends(get_current_user)):
    return ResponseModel[UserSchema](
        data=UserSchema.model_validate(current_user),
        message="User fetched successfully"
    )
