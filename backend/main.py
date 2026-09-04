from fastapi import FastAPI

app = FastAPI(title="AeroMind Backend")


@app.get("/health")
def health():
    return {"status": "ok", "service": "AeroMind Backend"}
