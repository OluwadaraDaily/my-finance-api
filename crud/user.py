# CRUD functions for user
from db.models.user import User
from db.session import get_db
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
  return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
  return db.query(User).filter(User.email == email).first()