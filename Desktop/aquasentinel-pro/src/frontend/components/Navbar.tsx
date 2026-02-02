"use client";

import { Droplet } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Droplet className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">AquaSentinel Pro</h1>
            <p className="text-xs text-gray-500">Early Warning System</p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <a href="/dashboard" className="text-sm font-medium text-gray-700 hover:text-blue-600">
            Dashboard
          </a>
          <a href="/" className="text-sm font-medium text-gray-700 hover:text-blue-600">
            Home
          </a>
        </div>
      </div>
    </nav>
  );
}
