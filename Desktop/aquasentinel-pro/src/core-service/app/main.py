from fastapi import FastAPI

from app.schemas import HealthResponse

app = FastAPI(title="AquaSentinel Core Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}
