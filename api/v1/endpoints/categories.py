from fastapi import APIRouter, Depends, HTTPException
from core.deps import get_current_user
from db.models.user import User
from db.session import get_db
from sqlalchemy.orm import Session
from services.category_service import CategoryService
from schemas.category import Category, CategoryCreate, CategoryUpdate
from typing import List

router = APIRouter()

@router.get("/", response_model=dict[str, object])
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    categories = category_service.get_categories(current_user.id)
    return {
        "data": [Category.model_validate(cat) for cat in categories],
        "message": "Categories fetched successfully"
    }

@router.get("/{category_id}", response_model=dict[str, object])
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    category = category_service.get_category(category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return {
        "data": Category.model_validate(category),
        "message": "Category fetched successfully"
    }

@router.post("/", response_model=dict[str, object])
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    category = category_service.create_category(current_user.id, category_data)
    return {
        "data": Category.model_validate(category),
        "message": "Category created successfully"
    }

@router.put("/{category_id}", response_model=dict[str, object])
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    category = category_service.update_category(category_id, current_user.id, category_data)
    return {
        "data": Category.model_validate(category),
        "message": "Category updated successfully"
    }

@router.delete("/{category_id}", response_model=dict[str, str])
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    response = category_service.delete_category(category_id, current_user.id)
    if response:
        return {
          "message": "Category deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Category not found")