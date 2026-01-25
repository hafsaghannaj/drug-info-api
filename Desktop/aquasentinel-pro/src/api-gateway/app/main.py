import os

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

CORE = os.getenv("CORE_SERVICE_URL", "http://localhost:8001")
ML = os.getenv("ML_SERVICE_URL", "http://localhost:8002")

app = FastAPI(title="AquaSentinel API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/core/health")
async def core_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CORE}/health")
        return r.json()


@app.post("/ml/predict")
async def ml_predict(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ML}/predict", json=payload)
        return r.json()
