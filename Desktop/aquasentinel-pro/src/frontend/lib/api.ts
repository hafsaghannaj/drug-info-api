/**
 * API Client for AquaSentinel Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Region {
  id: number;
  name: string;
  country: string;
  lat: number;
  lon: number;
  population: number;
  current_risk_level: string;
  current_risk_score: number;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: number;
  region_id: number;
  severity: string;
  disease_type: string;
  description: string;
  status: string;
  created_at: string;
  resolved_at?: string;
}

export interface Prediction {
  id: number;
  region_id: number;
  risk_score: number;
  confidence: number;
  factors: Record<string, any>;
  timestamp: string;
}

export interface AnalyticsSummary {
  total_regions_monitored: number;
  active_alerts: number;
  high_risk_regions: number;
  predictions_today: number;
  avg_risk_score: number;
  trend: string;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Regions
  async getRegions(): Promise<Region[]> {
    return this.request<Region[]>("/regions");
  }

  async getRegion(id: number): Promise<Region> {
    return this.request<Region>(`/regions/${id}`);
  }

  async getRegionPredictions(regionId: number, limit: number = 30): Promise<Prediction[]> {
    return this.request<Prediction[]>(`/regions/${regionId}/predictions?limit=${limit}`);
  }

  // Predictions
  async getPredictions(params?: {
    region_id?: number;
    days?: number;
  }): Promise<Prediction[]> {
    const queryParams = new URLSearchParams();
    if (params?.region_id) queryParams.append("region_id", params.region_id.toString());
    if (params?.days) queryParams.append("days", params.days.toString());

    const query = queryParams.toString();
    return this.request<Prediction[]>(`/predictions${query ? `?${query}` : ""}`);
  }

  async createPrediction(data: {
    region_id: number;
    risk_score: number;
    confidence: number;
    factors?: Record<string, any>;
  }): Promise<Prediction> {
    return this.request<Prediction>("/predictions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Alerts
  async getAlerts(params?: {
    status?: string;
    region_id?: number;
    limit?: number;
  }): Promise<Alert[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append("status", params.status);
    if (params?.region_id) queryParams.append("region_id", params.region_id.toString());
    if (params?.limit) queryParams.append("limit", params.limit.toString());

    const query = queryParams.toString();
    return this.request<Alert[]>(`/alerts${query ? `?${query}` : ""}`);
  }

  async getAlert(id: number): Promise<Alert> {
    return this.request<Alert>(`/alerts/${id}`);
  }

  async createAlert(data: {
    region_id: number;
    severity: string;
    disease_type: string;
    description: string;
  }): Promise<Alert> {
    return this.request<Alert>("/alerts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateAlert(
    id: number,
    data: { status?: string; resolved_at?: string }
  ): Promise<Alert> {
    return this.request<Alert>(`/alerts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Analytics
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    return this.request<AnalyticsSummary>("/analytics/summary");
  }

  async getRiskDistribution(): Promise<{
    low: number;
    medium: number;
    high: number;
    critical: number;
  }> {
    return this.request("/analytics/risk-distribution");
  }

  // ML Service
  async predictRisk(data: {
    region_id?: number;
    season?: string;
    recent_rainfall?: number;
    sanitation_index?: number;
    population_density?: number;
  }): Promise<{
    risk_score: number;
    confidence: number;
    top_factors: string[];
    region_id: number;
  }> {
    return this.request("/ml/predict", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
export const api = new APIClient(API_BASE_URL);
