"""
NASA GIBS (Global Imagery Browse Services) mock data provider
Simulates satellite imagery data for flood and rainfall monitoring
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List


class NASAGIBSProvider:
    """Mock provider for NASA satellite data"""

    @staticmethod
    def fetch_flood_data(region: str, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """
        Generate mock flood extent data from satellite imagery

        Args:
            region: Region name
            lat: Latitude
            lon: Longitude
            days: Number of days of historical data

        Returns:
            List of flood observation dictionaries
        """
        observations = []

        # Base flood extent varies by latitude (tropics have more flooding)
        base_extent = 50 + abs(lat) * 3

        for day_offset in range(days):
            date = datetime.utcnow() - timedelta(days=day_offset)

            # Add random variation
            extent = max(0, base_extent + random.uniform(-30, 80))

            observation = {
                "source": "NASA_GIBS",
                "region": region,
                "lat": lat,
                "lon": lon,
                "flood_extent_km2": round(extent, 2),
                "water_coverage_percent": min(100, round(extent / 10, 2)),
                "observation_date": date.isoformat(),
                "satellite": random.choice(["MODIS", "VIIRS", "Landsat-8"]),
                "cloud_coverage_percent": random.randint(0, 40),
            }

            observations.append(observation)

        return observations

    @staticmethod
    def fetch_rainfall_data(region: str, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """
        Generate mock rainfall data from satellite observations

        Args:
            region: Region name
            lat: Latitude
            lon: Longitude
            days: Number of days of historical data

        Returns:
            List of rainfall measurement dictionaries
        """
        measurements = []

        # Base rainfall varies by region (tropics = more rain)
        if abs(lat) < 23:  # Tropics
            base_rainfall = 150
        elif abs(lat) < 40:  # Subtropics
            base_rainfall = 80
        else:  # Temperate
            base_rainfall = 50

        for day_offset in range(days):
            date = datetime.utcnow() - timedelta(days=day_offset)

            # Add variation and occasional heavy rain events
            if random.random() < 0.15:  # 15% chance of heavy rain
                rainfall = base_rainfall + random.uniform(100, 300)
            else:
                rainfall = max(0, base_rainfall + random.uniform(-40, 80))

            measurement = {
                "source": "NASA_GIBS",
                "region": region,
                "lat": lat,
                "lon": lon,
                "rainfall_mm": round(rainfall, 1),
                "measurement_date": date.isoformat(),
                "data_product": "GPM_IMERG",  # Global Precipitation Measurement
                "quality_flag": random.choice(["good", "fair", "good", "good"]),
            }

            measurements.append(measurement)

        return measurements

    @staticmethod
    def fetch_vegetation_index(region: str, lat: float, lon: float) -> Dict:
        """
        Generate mock NDVI (vegetation health indicator)
        Can indicate environmental stress

        Args:
            region: Region name
            lat: Latitude
            lon: Longitude

        Returns:
            NDVI data dictionary
        """
        return {
            "source": "NASA_GIBS",
            "region": region,
            "lat": lat,
            "lon": lon,
            "ndvi": round(random.uniform(0.2, 0.8), 3),
            "observation_date": datetime.utcnow().isoformat(),
            "interpretation": "healthy" if random.random() > 0.3 else "stressed",
        }
