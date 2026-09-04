from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.alert import AlertResponse
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    is_read: bool | None = Query(None, description="Filter by read state"),
    db: Session = Depends(get_db),
):
    """List alerts, newest first."""
    return alert_service.get_alerts(db, is_read=is_read)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(alert_id: UUID, db: Session = Depends(get_db)):
    """Acknowledge an alert. Safe to call more than once."""
    alert = alert_service.mark_read(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
