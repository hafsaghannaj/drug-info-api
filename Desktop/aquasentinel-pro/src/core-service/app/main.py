from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.schemas import HealthResponse
from app.db import init_db, AsyncSessionLocal
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database and seed data
    print("Initializing database...")
    await init_db()

    # Seed database with mock data
    async with AsyncSessionLocal() as session:
        await seed_database(session)

    print("Core service ready!")
    yield
    # Shutdown
    print("Shutting down core service...")


app = FastAPI(
    title="AquaSentinel Core Service",
    version="1.0.0",
    lifespan=lifespan
)

# Import routers
from app.routes import regions, predictions, alerts, analytics

# Include routers
app.include_router(regions.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(analytics.router)


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}
