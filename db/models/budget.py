from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="budgets")
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="budgets")
    name = Column(String(255), index=True)
    description = Column(String(255), nullable=True)
    total_amount = Column(Integer, default=0)
    spent_amount = Column(Integer, default=0)
    remaining_amount = Column(Integer, default=0)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="budget")

    def __repr__(self):
        return f"<Budget {self.name}>"