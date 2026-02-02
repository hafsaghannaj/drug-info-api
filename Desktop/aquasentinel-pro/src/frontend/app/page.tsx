import { Droplet, MapPin, Bell, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      <div className="container mx-auto px-6 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <Droplet className="h-16 w-16 text-blue-600" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            AquaSentinel Pro
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Enterprise-grade early warning platform for waterborne disease
            outbreak prediction and monitoring
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Open Dashboard →
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <MapPin className="h-10 w-10 text-blue-600 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Global Monitoring</h3>
            <p className="text-gray-600 text-sm">
              Track waterborne disease risks across 20+ major urban regions
              worldwide in real-time
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <Bell className="h-10 w-10 text-orange-600 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Smart Alerts</h3>
            <p className="text-gray-600 text-sm">
              Receive instant notifications about disease outbreaks and
              elevated risk levels
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <TrendingUp className="h-10 w-10 text-green-600 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Predictive Analytics</h3>
            <p className="text-gray-600 text-sm">
              AI-powered risk predictions using satellite, weather, and health
              data
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
