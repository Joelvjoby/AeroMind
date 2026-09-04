from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mission import (
    MissionCreate,
    MissionDetailResponse,
    MissionReportResponse,
    MissionResponse,
)
from app.services import mission_service

router = APIRouter(prefix="/missions", tags=["missions"])


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(payload: MissionCreate, db: Session = Depends(get_db)):
    """Plan a new mission and store its route."""
    return mission_service.create_mission(db, payload)


@router.get("/{mission_id}", response_model=MissionDetailResponse)
def get_mission(mission_id: UUID, db: Session = Depends(get_db)):
    """Fetch a mission together with its ordered waypoints."""
    mission = mission_service.get_mission(db, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    return MissionDetailResponse(
        id=mission.id,
        name=mission.name,
        status=mission.status,
        created_at=mission.created_at,
        description=mission.description,
        waypoints=mission_service.get_mission_waypoints(db, mission_id),
    )


@router.get("/{mission_id}/report", response_model=MissionReportResponse)
def get_mission_report(mission_id: UUID, db: Session = Depends(get_db)):
    """Summarise a mission's tasks and alerts."""
    report = mission_service.get_mission_report(db, mission_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return report
