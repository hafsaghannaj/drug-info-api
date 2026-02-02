"""
WHO (World Health Organization) mock data provider
Simulates disease outbreak reports
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List


class WHOProvider:
    """Mock provider for WHO disease outbreak data"""

    DISEASES = [
        "cholera",
        "typhoid_fever",
        "dysentery",
        "hepatitis_a",
        "leptospirosis",
        "rotavirus",
        "norovirus",
    ]

    SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

    @staticmethod
    def fetch_outbreak_data(region: str, days: int = 7) -> List[Dict]:
        """
        Generate mock WHO outbreak reports for a region

        Args:
            region: Region name
            days: Number of days of historical data

        Returns:
            List of outbreak report dictionaries
        """
        reports = []

        for day_offset in range(days):
            date = datetime.utcnow() - timedelta(days=day_offset)

            # Random chance of having a report
            if random.random() < 0.6:  # 60% chance of report per day
                disease = random.choice(WHOProvider.DISEASES)
                cases = random.randint(10, 500)

                # Determine severity based on case count
                if cases > 300:
                    severity = "critical"
                elif cases > 150:
                    severity = "high"
                elif cases > 50:
                    severity = "medium"
                else:
                    severity = "low"

                report = {
                    "source": "WHO",
                    "region": region,
                    "disease": disease,
                    "cases": cases,
                    "deaths": random.randint(0, max(1, cases // 20)),
                    "severity": severity,
                    "report_date": date.isoformat(),
                    "description": f"{disease.replace('_', ' ').title()} outbreak detected in {region}",
                }

                reports.append(report)

        return reports

    @staticmethod
    def get_latest_alerts(region: str) -> List[Dict]:
        """
        Get latest disease alerts for a region

        Args:
            region: Region name

        Returns:
            List of active alerts
        """
        # Simulate 0-3 active alerts
        num_alerts = random.randint(0, 3)
        alerts = []

        for _ in range(num_alerts):
            disease = random.choice(WHOProvider.DISEASES)
            severity = random.choice(WHOProvider.SEVERITY_LEVELS[1:])  # medium to critical

            alert = {
                "source": "WHO",
                "region": region,
                "disease": disease,
                "severity": severity,
                "alert_level": random.randint(1, 3),
                "issued_at": (datetime.utcnow() - timedelta(days=random.randint(1, 5))).isoformat(),
                "active": True,
            }

            alerts.append(alert)

        return alerts
