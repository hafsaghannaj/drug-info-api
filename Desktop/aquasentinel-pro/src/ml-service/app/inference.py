"""
ML inference logic for risk prediction
"""
from typing import Dict, Any
from app.risk_factors import RiskFactorEngine


def predict_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate risk prediction based on input parameters

    Args:
        payload: Dictionary containing:
            - region_id (optional): Region identifier
            - season (optional): Season name
            - recent_rainfall (optional): Rainfall level 0-1
            - sanitation_index (optional): Sanitation quality 0-1
            - population_density (optional): Population density 0-1

    Returns:
        Dictionary with risk_score, confidence, and top_factors
    """

    # Extract parameters with defaults
    region_id = payload.get("region_id", 1)
    season = payload.get("season", "monsoon")
    recent_rainfall = payload.get("recent_rainfall", 0.6)
    sanitation_index = payload.get("sanitation_index", 0.5)
    population_density = payload.get("population_density", 0.7)

    # Calculate risk using factor engine
    risk_score, confidence, top_factors = RiskFactorEngine.calculate_risk(
        region_id=region_id,
        season=season,
        recent_rainfall=recent_rainfall,
        sanitation_index=sanitation_index,
        population_density=population_density,
    )

    return {
        "risk_score": round(risk_score, 2),
        "confidence": round(confidence, 2),
        "top_factors": top_factors,
        "region_id": region_id,
    }
