import { useState, useEffect } from "react";
import { api, Region } from "@/lib/api";

export function useRegions() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchRegions() {
      try {
        setLoading(true);
        const data = await api.getRegions();
        setRegions(data);
        setError(null);
      } catch (err) {
        setError(err as Error);
        console.error("Failed to fetch regions:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchRegions();
  }, []);

  return { regions, loading, error };
}
