from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from core.deps import get_current_user
from db.models.user import User
from db.session import get_db
from sqlalchemy.orm import Session
from services.pot_service import PotService
from schemas.pot import Pot, PotCreate, PotUpdate, UpdateSavedAmount, PotSummary
from schemas.common import ResponseModel, ListResponseModel

router = APIRouter()

@router.post("/", response_model=ResponseModel[Pot], status_code=status.HTTP_201_CREATED)
async def create_pot(
    pot_data: PotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new pot"""
    pot_service = PotService(db)
    pot = pot_service.create_pot(current_user.id, pot_data)
    return ResponseModel[Pot](
        data=pot,
        message="Pot created successfully"
    )

@router.get("/", response_model=ListResponseModel[Pot])
async def get_pots(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pots for the current user"""
    pot_service = PotService(db)
    pots = pot_service.get_pots(current_user.id, skip=skip, limit=limit)
    return ListResponseModel[Pot](
        data=pots,
        message="Pots fetched successfully"
    )

@router.get("/summary", response_model=ResponseModel[PotSummary])
async def get_pot_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the summary of all pots for the current user"""
    pot_service = PotService(db)
    summary = pot_service.get_pot_summary(current_user.id)
    return ResponseModel[PotSummary](
        data=summary,
        message="Pot summary fetched successfully"
    )

@router.get("/{pot_id}", response_model=ResponseModel[Pot])
async def get_pot(
    pot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific pot by ID"""
    pot_service = PotService(db)
    pot = pot_service.get_pot_by_id(pot_id, current_user.id)
    return ResponseModel[Pot](
        data=pot,
        message="Pot fetched successfully"
    )

@router.put("/{pot_id}", response_model=ResponseModel[Pot])
async def update_pot(
    pot_id: int,
    pot_data: PotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a pot's details"""
    pot_service = PotService(db)
    pot = pot_service.update_pot(pot_id, current_user.id, pot_data)
    return ResponseModel[Pot](
        data=pot,
        message="Pot updated successfully"
    )

@router.delete("/{pot_id}", response_model=ResponseModel[bool])
async def delete_pot(
    pot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a pot"""
    pot_service = PotService(db)
    result = pot_service.delete_pot(pot_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Pot not found")
    return ResponseModel[bool](
        data=result,
        message="Pot deleted successfully"
    )

@router.patch("/{pot_id}/update-saved-amount", response_model=ResponseModel[Pot])
async def update_saved_amount(
    pot_id: int,
    request: UpdateSavedAmount,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the saved amount of a pot"""
    pot_service = PotService(db)
    pot = pot_service.update_saved_amount(pot_id, current_user.id, request.amount)
    return ResponseModel[Pot](
        data=pot,
        message="Pot saved amount updated successfully"
    ) 