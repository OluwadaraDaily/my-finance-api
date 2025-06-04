from sqlalchemy.orm import Session
from db.models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate
from typing import List, Optional
from fastapi import HTTPException

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_categories(self, user_id: int) -> List[Category]:
        return self.db.query(Category).filter(Category.user_id == user_id).all()

    def get_category(self, category_id: int, user_id: int) -> Optional[Category]:
        category = self.db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category

    def create_category(self, user_id: int, category_data: CategoryCreate) -> Category:
        db_category = self.db.query(Category).filter(
            Category.name == category_data.name,
            Category.user_id == user_id
        ).first()
        if db_category:
            raise HTTPException(status_code=400, detail="Category already exists")
        db_category = Category(
            name=category_data.name,
            user_id=user_id,
            color=category_data.color
        )
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def update_category(self, category_id: int, user_id: int, category_data: CategoryUpdate) -> Category:
        category = self.get_category(category_id, user_id)
        for field, value in category_data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int, user_id: int) -> bool:
        category = self.get_category(category_id, user_id)
        self.db.delete(category)
        self.db.commit()
        return True