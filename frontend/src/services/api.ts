import { PredictionResult, SystemMetadata, ModelMetrics } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchMetadata(): Promise<SystemMetadata> {
  const res = await fetch(`${API_BASE}/metadata`);
  if (!res.ok) throw new Error("Failed to fetch metadata");
  return res.json();
}

export async function fetchObservations() {
  const res = await fetch(`${API_BASE}/observations`);
  if (!res.ok) throw new Error("Failed to fetch GMDA observations");
  return res.json();
}

export async function fetchAreas(minFsi?: number, classFilter?: string) {
  let url = `${API_BASE}/areas`;
  const params = new URLSearchParams();
  if (minFsi !== undefined) params.append("min_fsi", minFsi.toString());
  if (classFilter) params.append("class", classFilter);
  if (params.toString()) url += `?${params.toString()}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch areas GeoJSON");
  return res.json();
}

export async function fetchModelMetrics(): Promise<ModelMetrics> {
  const res = await fetch(`${API_BASE}/model/metrics`);
  if (!res.ok) throw new Error("Failed to fetch model metrics");
  return res.json();
}

export async function predictLocation(lat: number, lon: number): Promise<PredictionResult> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ latitude: lat, longitude: lon }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Prediction request failed");
  }
  return data;
}

export async function fetchPredictionsHistory() {
  const res = await fetch(`${API_BASE}/predictions`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "Failed to load prediction history");
  }
  return res.json();
}
