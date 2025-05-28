# CRUD functions for user
from typing import Optional, List
from sqlalchemy.orm import Session
from db.models.user import User
from schemas.user import UserCreate, UserUpdate

class UserCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user: UserCreate) -> User:
        """Create new user"""
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=user.password 
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update(self, user_id: int, user: UserUpdate) -> Optional[User]:
        """Update user"""
        db_user = self.get(user_id)
        if not db_user:
            return None
        
        update_data = user.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete(self, user_id: int) -> bool:
        """Delete user"""
        db_user = self.get(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True

    def get_active_users(self) -> List[User]:
        """Get all active users"""
        return self.db.query(User).filter(User.is_activated == True).all()

    def get_users_by_username(self, username: str) -> List[User]:
        """Get users by username (partial match)"""
        return self.db.query(User).filter(User.username.ilike(f"%{username}%")).all()