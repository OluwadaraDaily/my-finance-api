from typing import Optional, List
from sqlalchemy.orm import Session
from crud.user import UserCRUD
from schemas.user import UserCreate, UserUpdate, User as UserSchema
from fastapi import HTTPException, status
from db.models.user import User

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.crud = UserCRUD(db)

    def create_user(self, user: UserCreate) -> UserSchema:
        """Create user"""
        db_user = self.db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        return self.crud.create(user)

    def get_user(self, user_id: int) -> UserSchema:
        """Get user by ID"""
        db_user = self.crud.get(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserSchema.model_validate(db_user)

    def get_user_by_email(self, email: str) -> UserSchema:
        """Get user by email"""
        db_user = self.crud.get_by_email(email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserSchema.model_validate(db_user)

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserSchema]:
        """Get all users with pagination"""
        users = self.crud.get_all(skip=skip, limit=limit)
        return [UserSchema.model_validate(user) for user in users]

    def update_user(self, user_id: int, user: UserUpdate) -> UserSchema:
        """Update user"""
        db_user = self.crud.update(user_id, user)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserSchema.model_validate(db_user)

    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        if not self.crud.delete(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return True

    def get_active_users(self) -> List[UserSchema]:
        """Get all active users"""
        users = self.crud.get_active_users()
        return [UserSchema.model_validate(user) for user in users]

    def search_users_by_username(self, username: str) -> List[UserSchema]:
        """Search users by username (partial match)"""
        users = self.crud.get_users_by_username(username)
        return [UserSchema.model_validate(user) for user in users] 