"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MapPin,
  AlertTriangle,
  TrendingUp,
  Activity,
} from "lucide-react";

interface Stats {
  total_regions_monitored: number;
  active_alerts: number;
  high_risk_regions: number;
  predictions_today: number;
  avg_risk_score: number;
  trend: string;
}

export default function RegionStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch("/mock-data/stats.json")
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error("Failed to load stats:", err));
  }, []);

  if (!stats) {
    return <div className="text-gray-500">Loading stats...</div>;
  }

  const statCards = [
    {
      title: "Regions Monitored",
      value: stats.total_regions_monitored,
      icon: MapPin,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      title: "Active Alerts",
      value: stats.active_alerts,
      icon: AlertTriangle,
      color: "text-red-600",
      bgColor: "bg-red-50",
    },
    {
      title: "High Risk Regions",
      value: stats.high_risk_regions,
      icon: TrendingUp,
      color: "text-orange-600",
      bgColor: "bg-orange-50",
    },
    {
      title: "Predictions Today",
      value: stats.predictions_today,
      icon: Activity,
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((stat, index) => (
        <Card key={index}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  {stat.title}
                </p>
                <p className="text-3xl font-bold mt-2">{stat.value}</p>
              </div>
              <div className={`${stat.bgColor} p-3 rounded-lg`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
