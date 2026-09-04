import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import telemetry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

STREAM_INTERVAL_SECONDS = 1.0


@router.websocket("/stream")
async def stream_telemetry(websocket: WebSocket, drone_id: UUID | None = None):
    """Push a simulated telemetry sample once per second.

    Each sample drifts from the last, so the stream reads as a continuous
    flight. Samples are not persisted: they reference no real drone, and
    `telemetry_logs.drone_id` is a foreign key into `drones`.

    Websocket routes do not appear in the OpenAPI schema, so this endpoint
    is absent from /docs by design.
    """
    await websocket.accept()
    previous = None

    try:
        while True:
            previous = telemetry_service.generate_mock_telemetry(
                drone_id=drone_id, previous=previous
            )
            await websocket.send_text(previous.model_dump_json())
            await asyncio.sleep(STREAM_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")
