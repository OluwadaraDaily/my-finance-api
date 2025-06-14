from sqlalchemy.orm import Session
from db.models.pots import Pot
from db.models.transaction import Transaction
from schemas.pot import PotCreate, PotUpdate, PotSummary
from schemas.transaction import TransactionType, TransactionCreate
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime, timezone
from services.transaction_service import TransactionService
from db.models.user import User

class PotService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_service = TransactionService(db)

    def create_pot(self, user_id: int, pot_data: PotCreate) -> Pot:
        """Create a new pot for a user"""
        # Verify the pot does not already exist
        existing_pot = self.db.query(Pot).filter(
            Pot.name == pot_data.name,
            Pot.user_id == user_id
        ).first()
        if existing_pot:
            raise HTTPException(status_code=400, detail="Pot already exists")

        db_pot = Pot(
            user_id=user_id,
            name=pot_data.name,
            description=pot_data.description,
            target_amount=pot_data.target_amount,
            saved_amount=0,
            color=pot_data.color
        )
        self.db.add(db_pot)
        self.db.commit()
        self.db.refresh(db_pot)
        return db_pot

    def get_pots(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Pot]:
        """Get all pots for a user"""
        return (
            self.db.query(Pot)
            .filter(Pot.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pot_by_id(self, pot_id: int, user_id: int) -> Optional[Pot]:
        """Get a specific pot by ID"""
        pot = self.db.query(Pot).filter(
            Pot.id == pot_id,
            Pot.user_id == user_id
        ).first()
        if not pot:
            raise HTTPException(status_code=404, detail="Pot not found")
        return pot

    def update_pot(self, pot_id: int, user_id: int, pot_data: PotUpdate) -> Pot:
        """Update a pot's details"""
        pot = self.get_pot_by_id(pot_id, user_id)
        
        # Update the pot with the new data
        update_data = pot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pot, field, value)
        
        self.db.commit()
        self.db.refresh(pot)
        return pot

    def delete_pot(self, pot_id: int, user_id: int) -> bool:
        """Delete a pot"""
        pot = self.get_pot_by_id(pot_id, user_id)
        self.db.delete(pot)
        self.db.commit()
        return True

    def update_saved_amount(self, pot_id: int, user_id: int, user: User, amount: int, reason: str) -> Pot:
        """Update the saved amount of a pot and create a transaction record"""
        pot = self.get_pot_by_id(pot_id, user_id)
        
        # Ensure the new amount is not negative
        if pot.saved_amount + amount < 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot reduce saved amount below zero"
            )
        
        # Ensure the new amount is not greater than the target amount
        if pot.saved_amount + amount > pot.target_amount:
            raise HTTPException(
                status_code=400,
                detail="Cannot exceed target amount"
            )
        
        # Create transaction through transaction service
        transaction_data = TransactionCreate(
            amount=amount,
            description=reason,
            type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
            transaction_date=datetime.now(timezone.utc),
            pot_id=pot_id,
            sender="Self",
            recipient=pot.name,
        )
        self.transaction_service.create_transaction(transaction_data, user)
        
        # Update pot's saved amount
        pot.saved_amount += amount
        pot.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(pot)
        return pot

    def get_pot_summary(self, user_id: int) -> PotSummary:
        """Get the summary of all pots for a user"""
        pots = self.get_pots(user_id)
        total_saved_amount = sum(pot.saved_amount for pot in pots) if pots else 0
        total_target_amount = sum(pot.target_amount for pot in pots) if pots else 0
        average_progress = total_saved_amount / total_target_amount if total_target_amount > 0 else 0
        pots = self.get_pots(user_id, limit=4)
        return PotSummary(
            total_saved_amount=total_saved_amount, 
            total_target_amount=total_target_amount, 
            average_progress=average_progress,
            pots=pots
        )