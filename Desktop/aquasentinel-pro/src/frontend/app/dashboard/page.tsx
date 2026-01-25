"use client";

import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [risk, setRisk] = useState<any>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/ml/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ region: "demo" }),
    })
      .then((r) => r.json())
      .then(setRisk);
  }, []);

  return (
    <main className="p-8">
      <h2 className="text-2xl font-semibold">Risk Dashboard</h2>

      <div className="mt-6 rounded-2xl border p-4">
        <p className="font-medium">Live Risk Prediction</p>
        <pre className="mt-3 text-sm">{JSON.stringify(risk, null, 2)}</pre>
      </div>
    </main>
  );
}
