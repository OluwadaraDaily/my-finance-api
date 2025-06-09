from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum
from ..base import Base
from schemas.transaction import TransactionType

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String(255), nullable=True)
    recipient = Column(String(255), index=True, nullable=True)
    sender = Column(String(255), index=True, nullable=True)
    amount = Column(BigInteger)
    type = Column(Enum(TransactionType, name="transaction_type"), index=True)
    transaction_date = Column(DateTime, default=func.now())
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    budget = relationship("Budget", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.id}>"