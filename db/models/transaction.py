from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="transactions")
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="transactions")
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    budget = relationship("Budget", back_populates="transactions")
    description = Column(String(255), nullable=True)
    recipient = Column(String(255), index=True, nullable=True)
    sender = Column(String(255), index=True, nullable=True)
    amount = Column(Integer)
    type = Column(String(255), index=True)
    transaction_date = Column(DateTime, default=func.now()) # date of the transaction
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Transaction {self.id}>"