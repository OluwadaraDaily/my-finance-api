from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from datetime import timezone

class ActivationToken(Base):
    __tablename__ = "activation_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255), unique=True, index=True)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    user = relationship("User", back_populates="activation_token") 