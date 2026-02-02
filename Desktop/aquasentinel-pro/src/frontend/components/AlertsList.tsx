"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle } from "lucide-react";

interface Alert {
  id: number;
  region_name: string;
  severity: string;
  disease_type: string;
  description: string;
  created_at: string;
}

export default function AlertsList() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    fetch("/mock-data/alerts.json")
      .then((res) => res.json())
      .then((data) => setAlerts(data.slice(0, 5))) // Show top 5 alerts
      .catch((err) => console.error("Failed to load alerts:", err));
  }, []);

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case "critical":
        return "danger";
      case "high":
        return "warning";
      case "medium":
        return "secondary";
      default:
        return "default";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          Active Alerts
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No active alerts</p>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className="border-l-4 border-red-500 pl-4 py-2"
              >
                <div className="flex items-start justify-between mb-1">
                  <h4 className="font-semibold text-sm">{alert.region_name}</h4>
                  <Badge variant={getSeverityVariant(alert.severity)}>
                    {alert.severity}
                  </Badge>
                </div>
                <p className="text-xs text-gray-600 mb-1">
                  {alert.disease_type}
                </p>
                <p className="text-xs text-gray-500">{alert.description}</p>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
