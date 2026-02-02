"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import MapLegend from "./MapLegend";

// Dynamically import Leaflet components to avoid SSR issues
const MapContainer = dynamic(
  () => import("react-leaflet").then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import("react-leaflet").then((mod) => mod.TileLayer),
  { ssr: false }
);
const CircleMarker = dynamic(
  () => import("react-leaflet").then((mod) => mod.CircleMarker),
  { ssr: false }
);
const Popup = dynamic(
  () => import("react-leaflet").then((mod) => mod.Popup),
  { ssr: false }
);

interface Region {
  id: number;
  name: string;
  country: string;
  lat: number;
  lon: number;
  population: number;
  current_risk_level: string;
  risk_score: number;
}

export default function RiskMap() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Fetch regions data
    fetch("/mock-data/regions.json")
      .then((res) => res.json())
      .then((data) => setRegions(data))
      .catch((err) => console.error("Failed to load regions:", err));
  }, []);

  const getRiskColor = (riskScore: number) => {
    if (riskScore >= 0.8) return "#dc2626"; // red-600
    if (riskScore >= 0.6) return "#f97316"; // orange-500
    if (riskScore >= 0.4) return "#eab308"; // yellow-500
    return "#22c55e"; // green-500
  };

  if (!mounted) {
    return (
      <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">Loading map...</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full rounded-lg overflow-hidden">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {regions.map((region) => (
          <CircleMarker
            key={region.id}
            center={[region.lat, region.lon]}
            radius={8 + region.risk_score * 12}
            fillColor={getRiskColor(region.risk_score)}
            color="#fff"
            weight={2}
            opacity={0.9}
            fillOpacity={0.7}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-base">{region.name}</h3>
                <p className="text-sm text-gray-600">{region.country}</p>
                <div className="mt-2 space-y-1">
                  <p className="text-sm">
                    <span className="font-semibold">Risk Score:</span>{" "}
                    {(region.risk_score * 100).toFixed(0)}%
                  </p>
                  <p className="text-sm">
                    <span className="font-semibold">Level:</span>{" "}
                    <span className="capitalize">{region.current_risk_level}</span>
                  </p>
                  <p className="text-sm">
                    <span className="font-semibold">Population:</span>{" "}
                    {(region.population / 1000000).toFixed(1)}M
                  </p>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <MapLegend />
    </div>
  );
}
