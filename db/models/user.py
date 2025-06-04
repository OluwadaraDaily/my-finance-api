# SQLAlchemy User model

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_activated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    accounts = relationship("Account", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    user_auth = relationship("UserAuth", back_populates="user")
    activation_token = relationship("ActivationToken", back_populates="user", uselist=False)
    api_keys = relationship("APIKey", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"