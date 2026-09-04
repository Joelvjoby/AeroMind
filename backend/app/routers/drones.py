from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.drone import DroneResponse
from app.services import drone_service

router = APIRouter(prefix="/drones", tags=["drones"])


@router.get("", response_model=list[DroneResponse])
def list_drones(db: Session = Depends(get_db)):
    """List every drone in the fleet with its current status and FSM state."""
    return drone_service.get_fleet_status(db)
