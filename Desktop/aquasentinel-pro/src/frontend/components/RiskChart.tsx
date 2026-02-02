"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface PredictionData {
  date: string;
  [key: string]: number | string;
}

export default function RiskChart() {
  const [data, setData] = useState<PredictionData[]>([]);

  useEffect(() => {
    fetch("/mock-data/predictions.json")
      .then((res) => res.json())
      .then((predictions) => setData(predictions))
      .catch((err) => console.error("Failed to load predictions:", err));
  }, []);

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }}
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
          />
          <Tooltip
            formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="Mumbai"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="Dhaka"
            stroke="#dc2626"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="Lagos"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="Jakarta"
            stroke="#eab308"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="Manila"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
