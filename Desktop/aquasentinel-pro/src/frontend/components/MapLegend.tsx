"use client";

export default function MapLegend() {
  return (
    <div className="absolute bottom-6 left-6 z-[1000] bg-white rounded-lg shadow-lg p-4 border">
      <h3 className="text-sm font-semibold mb-3">Risk Levels</h3>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-600"></div>
          <span className="text-xs">Critical (0.8+)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-orange-500"></div>
          <span className="text-xs">High (0.6-0.8)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
          <span className="text-xs">Medium (0.4-0.6)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span className="text-xs">Low (&lt;0.4)</span>
        </div>
      </div>
    </div>
  );
}
