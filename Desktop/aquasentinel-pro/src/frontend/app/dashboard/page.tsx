"use client";

import dynamic from "next/dynamic";
import Navbar from "@/components/Navbar";
import RegionStats from "@/components/RegionStats";
import AlertsList from "@/components/AlertsList";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Dynamically import map to avoid SSR issues
const RiskMap = dynamic(() => import("@/components/RiskMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-gray-100 rounded-lg flex items-center justify-center">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

const RiskChart = dynamic(() => import("@/components/RiskChart"), {
  ssr: false,
});

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="p-6 space-y-6">
        {/* Stats Grid */}
        <RegionStats />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map - Takes 2 columns on large screens */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Global Risk Map</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[500px]">
                <RiskMap />
              </div>
            </CardContent>
          </Card>

          {/* Alerts List - Takes 1 column */}
          <div className="space-y-6">
            <AlertsList />
          </div>
        </div>

        {/* Risk Trends Chart */}
        <Card>
          <CardHeader>
            <CardTitle>30-Day Risk Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[350px]">
              <RiskChart />
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
