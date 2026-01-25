from fastapi import FastAPI

app = FastAPI(title="AquaSentinel Ingestion Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ingest/run")
async def run_ingestion():
    # Placeholder: will fetch from NASA/NOAA/WHO and publish to NATS
    return {"status": "started"}
