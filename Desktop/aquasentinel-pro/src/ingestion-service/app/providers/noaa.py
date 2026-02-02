"""
NOAA (National Oceanic and Atmospheric Administration) mock data provider
Simulates weather and climate data
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List


class NOAAProvider:
    """Mock provider for NOAA weather and climate data"""

    @staticmethod
    def fetch_weather_data(region: str, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """
        Generate mock weather observations

        Args:
            region: Region name
            lat: Latitude
            lon: Longitude
            days: Number of days of historical data

        Returns:
            List of weather observation dictionaries
        """
        observations = []

        # Base temperature varies by latitude
        if abs(lat) < 23:  # Tropics
            base_temp = 28
        elif abs(lat) < 40:  # Subtropics
            base_temp = 22
        else:  # Temperate
            base_temp = 15

        for day_offset in range(days):
            date = datetime.utcnow() - timedelta(days=day_offset)

            observation = {
                "source": "NOAA",
                "region": region,
                "lat": lat,
                "lon": lon,
                "temperature_c": round(base_temp + random.uniform(-5, 8), 1),
                "humidity_percent": random.randint(60, 95),
                "pressure_mb": random.randint(995, 1020),
                "wind_speed_kmh": random.randint(5, 45),
                "observation_date": date.isoformat(),
                "conditions": random.choice([
                    "clear", "partly_cloudy", "cloudy", "rain", "heavy_rain", "thunderstorm"
                ]),
            }

            observations.append(observation)

        return observations

    @staticmethod
    def fetch_precipitation_forecast(region: str, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """
        Generate mock precipitation forecast

        Args:
            region: Region name
            lat: Latitude
            lon: Longitude
            days: Number of forecast days

        Returns:
            List of forecast dictionaries
        """
        forecasts = []

        for day_offset in range(days):
            date = datetime.utcnow() + timedelta(days=day_offset)

            # Generate forecast
            precip_prob = random.randint(10, 90)

            if precip_prob > 70:
                forecast_level = "high"
                expected_mm = random.randint(50, 200)
            elif precip_prob > 40:
                forecast_level = "medium"
                expected_mm = random.randint(20, 60)
            else:
                forecast_level = "low"
                expected_mm = random.randint(0, 25)

            forecast = {
                "source": "NOAA",
                "region": region,
                "lat": lat,
                "lon": lon,
                "forecast_date": date.isoformat(),
                "precipitation_probability": precip_prob,
                "precipitation_forecast": forecast_level,
                "expected_precipitation_mm": expected_mm,
                "confidence": random.choice(["low", "medium", "high", "high"]),
            }

            forecasts.append(forecast)

        return forecasts

    @staticmethod
    def fetch_climate_anomalies(region: str, lat: float, lon: float) -> Dict:
        """
        Generate mock climate anomaly data

        Args:
            region: Region name
            lat: Latitude
            lon: Longitude

        Returns:
            Climate anomaly dictionary
        """
        return {
            "source": "NOAA",
            "region": region,
            "lat": lat,
            "lon": lon,
            "temperature_anomaly_c": round(random.uniform(-2, 3), 1),
            "precipitation_anomaly_percent": round(random.uniform(-30, 50), 1),
            "sea_surface_temp_anomaly_c": round(random.uniform(-1, 2), 1),
            "analysis_period": "30_day",
            "report_date": datetime.utcnow().isoformat(),
        }
