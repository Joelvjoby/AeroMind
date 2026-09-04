from fastapi import FastAPI

from app.routers import alerts, drones, missions, telemetry

API_PREFIX = "/api/v1"

app = FastAPI(title="AeroMind Backend")

app.include_router(missions.router, prefix=API_PREFIX)
app.include_router(drones.router, prefix=API_PREFIX)
app.include_router(telemetry.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "service": "AeroMind Backend"}
