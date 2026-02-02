import os

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

CORE = os.getenv("CORE_SERVICE_URL", "http://localhost:8001")
ML = os.getenv("ML_SERVICE_URL", "http://localhost:8002")
INGESTION = os.getenv("INGESTION_SERVICE_URL", "http://localhost:8003")

app = FastAPI(title="AquaSentinel API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Core Service Proxy Routes
@app.get("/core/health")
async def core_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CORE}/health")
        return r.json()


@app.api_route("/regions/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_regions(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{CORE}/regions/{path}" if path else f"{CORE}/regions"
        if request.method == "GET":
            # Forward query params
            r = await client.get(url, params=request.query_params)
        else:
            body = await request.json() if await request.body() else {}
            r = await client.request(request.method, url, json=body)
        return JSONResponse(content=r.json(), status_code=r.status_code)


@app.get("/regions")
async def get_regions(request: Request):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CORE}/regions", params=request.query_params)
        return r.json()


@app.api_route("/predictions/{path:path}", methods=["GET", "POST"])
async def proxy_predictions(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{CORE}/predictions/{path}" if path else f"{CORE}/predictions"
        if request.method == "GET":
            r = await client.get(url, params=request.query_params)
        else:
            body = await request.json()
            r = await client.post(url, json=body)
        return JSONResponse(content=r.json(), status_code=r.status_code)


@app.get("/predictions")
async def get_predictions(request: Request):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CORE}/predictions", params=request.query_params)
        return r.json()


@app.api_route("/alerts/{path:path}", methods=["GET", "POST", "PATCH"])
async def proxy_alerts(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{CORE}/alerts/{path}" if path else f"{CORE}/alerts"
        if request.method == "GET":
            r = await client.get(url, params=request.query_params)
        else:
            body = await request.json()
            r = await client.request(request.method, url, json=body)
        return JSONResponse(content=r.json(), status_code=r.status_code)


@app.get("/alerts")
async def get_alerts(request: Request):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{CORE}/alerts", params=request.query_params)
        return r.json()


@app.get("/analytics/{path:path}")
async def proxy_analytics(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{CORE}/analytics/{path}"
        r = await client.get(url, params=request.query_params)
        return r.json()


# ML Service Proxy Routes
@app.post("/ml/predict")
async def ml_predict(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ML}/predict", json=payload)
        return r.json()


# Ingestion Service Proxy Routes
@app.post("/ingest/run")
async def trigger_ingestion(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{INGESTION}/ingest/run", json=payload)
        return r.json()
