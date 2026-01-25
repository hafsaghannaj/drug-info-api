from fastapi import FastAPI

app = FastAPI(title="AquaSentinel ML Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(payload: dict):
    # Placeholder: real version will load models from MLflow registry
    return {
        "risk_score": 0.73,
        "confidence": 0.81,
        "top_factors": ["rainfall_anomaly", "flood_extent", "low_sanitation"],
    }
