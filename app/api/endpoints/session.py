from fastapi import APIRouter, HTTPException
from typing import List
from app.crud.crud_session import get_last_session, get_session
from app.models.session import Session
from app.models.supplier import Supplier

router = APIRouter()

@router.get("/last-session", response_model=Session)
async def get_last_session_endpoint():
    """
    Get the last created session
    """
    session = await get_last_session()
    if not session:
        raise HTTPException(status_code=404, detail="No sessions found")
    return session

@router.get("/suppliers", response_model=List[Supplier])
async def get_all_suppliers_of_session():
    """
    Get all suppliers for a specific session
    """
    session = await get_last_session()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.suppliers 