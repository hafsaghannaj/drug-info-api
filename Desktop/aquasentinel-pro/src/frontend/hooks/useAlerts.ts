import { useState, useEffect } from "react";
import { api, Alert } from "@/lib/api";

interface UseAlertsOptions {
  status?: string;
  region_id?: number;
  limit?: number;
}

export function useAlerts(options?: UseAlertsOptions) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchAlerts() {
      try {
        setLoading(true);
        const data = await api.getAlerts(options);
        setAlerts(data);
        setError(null);
      } catch (err) {
        setError(err as Error);
        console.error("Failed to fetch alerts:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchAlerts();
  }, [options?.status, options?.region_id, options?.limit]);

  return { alerts, loading, error };
}
