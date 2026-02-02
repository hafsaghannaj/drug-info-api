from fastapi import FastAPI
from app.inference import predict_risk

app = FastAPI(title="AquaSentinel ML Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(payload: dict):
    """
    Predict waterborne disease risk based on environmental factors

    Accepts:
        - region_id (int): Region identifier
        - season (str): Season (monsoon, dry, wet)
        - recent_rainfall (float): Rainfall level 0-1
        - sanitation_index (float): Sanitation quality 0-1 (higher is better)
        - population_density (float): Population density 0-1

    Returns:
        - risk_score (float): Overall risk score 0-1
        - confidence (float): Prediction confidence 0-1
        - top_factors (list): Top 3 contributing risk factors
        - region_id (int): Region ID
    """
    return predict_risk(payload)
