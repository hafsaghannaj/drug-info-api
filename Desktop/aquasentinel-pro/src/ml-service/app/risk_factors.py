"""
Risk factor calculation logic for waterborne disease prediction
"""
import random
from typing import Dict, List, Tuple


class RiskFactorEngine:
    """Calculate risk scores based on multiple environmental and health factors"""

    # Factor weights (must sum to 1.0)
    WEIGHTS = {
        "rainfall_anomaly": 0.30,
        "sanitation_index": 0.25,
        "population_density": 0.20,
        "flood_extent": 0.15,
        "water_quality": 0.10,
    }

    @staticmethod
    def calculate_risk(
        region_id: int = 1,
        season: str = "monsoon",
        recent_rainfall: float = 0.5,
        sanitation_index: float = 0.5,
        population_density: float = 0.5,
    ) -> Tuple[float, float, List[str]]:
        """
        Calculate risk score based on input parameters

        Args:
            region_id: ID of the region
            season: Season (monsoon, dry, wet)
            recent_rainfall: Rainfall level (0-1)
            sanitation_index: Sanitation quality (0-1, higher is better)
            population_density: Population density factor (0-1)

        Returns:
            (risk_score, confidence, top_factors)
        """

        # Calculate individual factor scores
        rainfall_factor = RiskFactorEngine._rainfall_risk(recent_rainfall, season)
        sanitation_factor = RiskFactorEngine._sanitation_risk(sanitation_index)
        density_factor = RiskFactorEngine._density_risk(population_density)
        flood_factor = RiskFactorEngine._flood_risk(recent_rainfall)
        water_quality_factor = RiskFactorEngine._water_quality_risk(
            sanitation_index, recent_rainfall
        )

        # Weighted risk score
        risk_score = (
            rainfall_factor * RiskFactorEngine.WEIGHTS["rainfall_anomaly"]
            + sanitation_factor * RiskFactorEngine.WEIGHTS["sanitation_index"]
            + density_factor * RiskFactorEngine.WEIGHTS["population_density"]
            + flood_factor * RiskFactorEngine.WEIGHTS["flood_extent"]
            + water_quality_factor * RiskFactorEngine.WEIGHTS["water_quality"]
        )

        # Clamp to [0, 1]
        risk_score = max(0.0, min(1.0, risk_score))

        # Calculate confidence (higher when factors are extreme)
        factor_variance = RiskFactorEngine._calculate_variance([
            rainfall_factor,
            sanitation_factor,
            density_factor,
            flood_factor,
            water_quality_factor,
        ])
        confidence = 0.7 + (0.25 * (1 - factor_variance))

        # Identify top contributing factors
        factors = {
            "rainfall_anomaly": rainfall_factor,
            "sanitation_index": sanitation_factor,
            "population_density": density_factor,
            "flood_extent": flood_factor,
            "water_quality": water_quality_factor,
        }
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]
        top_factor_names = [f[0] for f in top_factors]

        return risk_score, confidence, top_factor_names

    @staticmethod
    def _rainfall_risk(rainfall: float, season: str) -> float:
        """Calculate risk from rainfall patterns"""
        base_risk = rainfall

        # Increase risk during monsoon season
        if season == "monsoon":
            base_risk = min(1.0, rainfall * 1.3)
        elif season == "dry":
            base_risk = rainfall * 0.7

        return base_risk

    @staticmethod
    def _sanitation_risk(sanitation: float) -> float:
        """Calculate risk from sanitation index (inverted - low sanitation = high risk)"""
        return 1.0 - sanitation

    @staticmethod
    def _density_risk(density: float) -> float:
        """Calculate risk from population density"""
        # Non-linear: higher density exponentially increases risk
        return min(1.0, density ** 0.8)

    @staticmethod
    def _flood_risk(rainfall: float) -> float:
        """Estimate flood risk from rainfall"""
        # Floods more likely with very high rainfall
        if rainfall > 0.7:
            return min(1.0, (rainfall - 0.5) * 1.5)
        return rainfall * 0.5

    @staticmethod
    def _water_quality_risk(sanitation: float, rainfall: float) -> float:
        """Estimate water quality risk from sanitation and rainfall"""
        # Poor sanitation + high rainfall = contaminated water
        base_risk = (1.0 - sanitation) * 0.6 + rainfall * 0.4
        return min(1.0, base_risk)

    @staticmethod
    def _calculate_variance(values: List[float]) -> float:
        """Calculate normalized variance of factor values"""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)

        # Normalize to [0, 1]
        return min(1.0, variance * 4)
