from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base

class Pot(Base):
    __tablename__ = "pots"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), index=True)
    description = Column(String(255), nullable=True)
    target_amount = Column(Integer, default=0)
    saved_amount = Column(Integer, default=0)
    color = Column(String(255), default="#000000")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="pots")
    transactions = relationship("Transaction", back_populates="pot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pot {self.name}>"