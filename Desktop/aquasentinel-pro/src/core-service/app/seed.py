from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Region, RiskPrediction, Alert, DataSource, RiskLevel, Severity, AlertStatus


async def seed_database(session: AsyncSession):
    """Seed the database with initial mock data"""

    # Check if data already exists
    from sqlalchemy import select
    result = await session.execute(select(Region))
    if result.scalars().first():
        print("Database already seeded, skipping...")
        return

    print("Seeding database with mock data...")

    # Seed Regions
    regions_data = [
        {"name": "Mumbai", "country": "India", "lat": 19.076, "lon": 72.8777, "population": 20961472, "risk_level": RiskLevel.HIGH, "risk_score": 0.78},
        {"name": "Dhaka", "country": "Bangladesh", "lat": 23.8103, "lon": 90.4125, "population": 21005860, "risk_level": RiskLevel.CRITICAL, "risk_score": 0.89},
        {"name": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "population": 14862000, "risk_level": RiskLevel.HIGH, "risk_score": 0.72},
        {"name": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lon": 106.8456, "population": 10770000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.56},
        {"name": "Manila", "country": "Philippines", "lat": 14.5995, "lon": 120.9842, "population": 13923000, "risk_level": RiskLevel.HIGH, "risk_score": 0.68},
        {"name": "Nairobi", "country": "Kenya", "lat": -1.2921, "lon": 36.8219, "population": 4922000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.54},
        {"name": "Karachi", "country": "Pakistan", "lat": 24.8607, "lon": 67.0011, "population": 16093000, "risk_level": RiskLevel.HIGH, "risk_score": 0.75},
        {"name": "Lima", "country": "Peru", "lat": -12.0464, "lon": -77.0428, "population": 10719000, "risk_level": RiskLevel.LOW, "risk_score": 0.32},
        {"name": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "population": 20900000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.48},
        {"name": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "population": 14850000, "risk_level": RiskLevel.HIGH, "risk_score": 0.71},
        {"name": "Kinshasa", "country": "DR Congo", "lat": -4.4419, "lon": 15.2663, "population": 14970000, "risk_level": RiskLevel.CRITICAL, "risk_score": 0.85},
        {"name": "Dar es Salaam", "country": "Tanzania", "lat": -6.7924, "lon": 39.2083, "population": 6702000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.59},
        {"name": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "population": 10539000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.51},
        {"name": "Hanoi", "country": "Vietnam", "lat": 21.0285, "lon": 105.8542, "population": 8246000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.47},
        {"name": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "population": 22043000, "risk_level": RiskLevel.LOW, "risk_score": 0.28},
        {"name": "Yangon", "country": "Myanmar", "lat": 16.8661, "lon": 96.1951, "population": 5430000, "risk_level": RiskLevel.HIGH, "risk_score": 0.69},
        {"name": "Accra", "country": "Ghana", "lat": 5.6037, "lon": -0.187, "population": 2475000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.52},
        {"name": "Port-au-Prince", "country": "Haiti", "lat": 18.5944, "lon": -72.3074, "population": 2987000, "risk_level": RiskLevel.CRITICAL, "risk_score": 0.92},
        {"name": "Addis Ababa", "country": "Ethiopia", "lat": 9.03, "lon": 38.74, "population": 4794000, "risk_level": RiskLevel.MEDIUM, "risk_score": 0.58},
        {"name": "Chittagong", "country": "Bangladesh", "lat": 22.3569, "lon": 91.7832, "population": 5252000, "risk_level": RiskLevel.HIGH, "risk_score": 0.73},
    ]

    regions = []
    for data in regions_data:
        region = Region(
            name=data["name"],
            country=data["country"],
            lat=data["lat"],
            lon=data["lon"],
            population=data["population"],
            current_risk_level=data["risk_level"],
            current_risk_score=data["risk_score"]
        )
        session.add(region)
        regions.append(region)

    await session.flush()  # Flush to get IDs
    print(f"Seeded {len(regions)} regions")

    # Seed Historical Risk Predictions (past 30 days)
    predictions = []
    diseases = ["cholera", "typhoid", "dysentery", "hepatitis_a", "leptospirosis"]

    for region in regions:
        # Create predictions for past 30 days
        for days_ago in range(30, 0, -3):  # Every 3 days
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            # Vary risk score slightly around current level
            base_score = region.current_risk_score
            variance = random.uniform(-0.1, 0.1)
            risk_score = max(0.0, min(1.0, base_score + variance))

            prediction = RiskPrediction(
                region_id=region.id,
                risk_score=risk_score,
                confidence=random.uniform(0.75, 0.95),
                factors={
                    "rainfall_anomaly": random.uniform(0, 1),
                    "flood_extent": random.uniform(0, 1),
                    "sanitation_index": random.uniform(0, 1),
                    "population_density": random.uniform(0, 1),
                    "historical_outbreaks": random.uniform(0, 1)
                },
                timestamp=timestamp
            )
            session.add(prediction)
            predictions.append(prediction)

    await session.flush()
    print(f"Seeded {len(predictions)} historical predictions")

    # Seed Active Alerts
    alerts_data = [
        {"region_idx": 1, "severity": Severity.CRITICAL, "disease": "Cholera", "desc": "Severe cholera outbreak detected. 450+ confirmed cases in the past week."},
        {"region_idx": 17, "severity": Severity.CRITICAL, "disease": "Typhoid Fever", "desc": "Major typhoid fever outbreak following recent flooding. 300+ cases reported."},
        {"region_idx": 10, "severity": Severity.CRITICAL, "disease": "Cholera", "desc": "Ongoing cholera epidemic. Sanitation infrastructure severely compromised."},
        {"region_idx": 0, "severity": Severity.HIGH, "disease": "Hepatitis A", "desc": "Hepatitis A outbreak linked to contaminated water supply. 120 cases confirmed."},
        {"region_idx": 2, "severity": Severity.HIGH, "disease": "Cholera", "desc": "Cholera cases rising in coastal areas. 85 confirmed cases this week."},
        {"region_idx": 6, "severity": Severity.HIGH, "disease": "Dysentery", "desc": "Bacterial dysentery outbreak in northern districts. 95 cases reported."},
        {"region_idx": 4, "severity": Severity.HIGH, "disease": "Leptospirosis", "desc": "Post-typhoon leptospirosis outbreak. 78 confirmed cases."},
        {"region_idx": 9, "severity": Severity.HIGH, "disease": "Cholera", "desc": "Seasonal cholera spike detected. 60+ cases in slum areas."},
        {"region_idx": 15, "severity": Severity.HIGH, "disease": "Typhoid Fever", "desc": "Typhoid fever outbreak in eastern townships. 52 confirmed cases."},
        {"region_idx": 19, "severity": Severity.HIGH, "disease": "Cholera", "desc": "Cholera cases increasing after heavy monsoon rains. 48 cases reported."},
    ]

    alerts = []
    for alert_data in alerts_data:
        region = regions[alert_data["region_idx"]]
        alert = Alert(
            region_id=region.id,
            severity=alert_data["severity"],
            disease_type=alert_data["disease"],
            description=alert_data["desc"],
            status=AlertStatus.ACTIVE,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 5))
        )
        session.add(alert)
        alerts.append(alert)

    await session.flush()
    print(f"Seeded {len(alerts)} active alerts")

    # Seed Data Source entries
    data_sources = []
    source_types = ["WHO", "NASA_GIBS", "NOAA"]

    for region in regions[:10]:  # Add data sources for first 10 regions
        for source_type in source_types:
            for days_ago in range(7, 0, -1):  # Past week
                if source_type == "WHO":
                    payload = {
                        "disease": random.choice(diseases),
                        "cases": random.randint(10, 200),
                        "severity": random.choice(["low", "medium", "high"])
                    }
                elif source_type == "NASA_GIBS":
                    payload = {
                        "flood_extent_km2": random.randint(50, 500),
                        "rainfall_mm": random.randint(50, 300)
                    }
                else:  # NOAA
                    payload = {
                        "temperature": random.randint(20, 35),
                        "humidity": random.randint(60, 95),
                        "precipitation_forecast": random.choice(["low", "medium", "high"])
                    }

                data_source = DataSource(
                    region_id=region.id,
                    source_type=source_type,
                    data_payload=payload,
                    ingested_at=datetime.utcnow() - timedelta(days=days_ago)
                )
                session.add(data_source)
                data_sources.append(data_source)

    await session.commit()
    print(f"Seeded {len(data_sources)} data source entries")
    print("Database seeding completed successfully!")
