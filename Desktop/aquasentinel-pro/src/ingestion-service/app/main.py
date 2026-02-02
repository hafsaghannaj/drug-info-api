from fastapi import FastAPI
from app.providers.who import WHOProvider
from app.providers.nasa_gibs import NASAGIBSProvider
from app.providers.noaa import NOAAProvider

app = FastAPI(title="AquaSentinel Ingestion Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ingest/run")
async def run_ingestion(payload: dict):
    """
    Run data ingestion from all providers for a region

    Accepts:
        - region (str): Region name
        - lat (float): Latitude
        - lon (float): Longitude
        - days (int, optional): Days of historical data

    Returns:
        Aggregated data from all sources
    """
    region = payload.get("region", "Mumbai")
    lat = payload.get("lat", 19.076)
    lon = payload.get("lon", 72.8777)
    days = payload.get("days", 7)

    # Fetch data from all providers
    who_outbreaks = WHOProvider.fetch_outbreak_data(region, days)
    who_alerts = WHOProvider.get_latest_alerts(region)

    nasa_floods = NASAGIBSProvider.fetch_flood_data(region, lat, lon, days)
    nasa_rainfall = NASAGIBSProvider.fetch_rainfall_data(region, lat, lon, days)
    nasa_vegetation = NASAGIBSProvider.fetch_vegetation_index(region, lat, lon)

    noaa_weather = NOAAProvider.fetch_weather_data(region, lat, lon, days)
    noaa_forecast = NOAAProvider.fetch_precipitation_forecast(region, lat, lon, days)
    noaa_anomalies = NOAAProvider.fetch_climate_anomalies(region, lat, lon)

    return {
        "status": "completed",
        "region": region,
        "data": {
            "who": {
                "outbreaks": who_outbreaks,
                "alerts": who_alerts,
            },
            "nasa_gibs": {
                "floods": nasa_floods,
                "rainfall": nasa_rainfall,
                "vegetation": nasa_vegetation,
            },
            "noaa": {
                "weather": noaa_weather,
                "forecast": noaa_forecast,
                "anomalies": noaa_anomalies,
            },
        },
        "ingestion_timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }
