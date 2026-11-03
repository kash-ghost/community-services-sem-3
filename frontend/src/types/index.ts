export interface FeatureContribution {
  [key: string]: number;
}

export interface FeatureValues {
  elevation_m?: number | null;
  slope_deg?: number | null;
  built_up_frac?: number | null;
  veg_frac?: number | null;
  water_frac?: number | null;
  dist_to_water_m?: number | null;
  dist_to_drain_m?: number | null;
  monsoon_rainfall_mm?: number | null;
}

export interface PredictionResult {
  prediction_id: string;
  timestamp?: string;
  model_version: string;
  prediction_mode: string;
  input: {
    latitude: number;
    longitude: number;
  };
  cell_id: string;
  result: {
    fsi: number;
    fsi_class: "low" | "moderate" | "high" | "very_high" | "unknown";
    fsi_class_label: string;
  };
  features: FeatureValues;
  feature_contributions: FeatureContribution;
  limitations: string[];
}

export interface DatasetItem {
  id: string;
  name: string;
  type: string;
  status: string;
  records?: number;
}

export interface SystemMetadata {
  study_area: {
    name: string;
    bbox: [number, number, number, number];
    crs: string;
    projected_crs: string;
  };
  prediction_unit: string;
  prediction_mode: string;
  model_version: string;
  datasets: DatasetItem[];
  supervised_ml_feasible: boolean;
  supervised_ml_rationale: string;
  last_updated: string;
}

export interface GMDAPoint {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: {
    objectid: number;
    surveytype: string;
    waterloggingtype?: string;
    zone?: string;
    sector?: string;
    remarks?: string;
    surveydate?: string | null;
  };
}

export interface GridCellFeature {
  type: "Feature";
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  properties: {
    cell_id: string;
    centroid_lon: number;
    centroid_lat: number;
    elevation_m?: number;
    slope_deg?: number;
    built_up_frac?: number;
    veg_frac?: number;
    water_frac?: number;
    dist_to_water_m?: number;
    dist_to_drain_m?: number;
    monsoon_rainfall_mm?: number;
    fsi: number;
    fsi_class: "low" | "moderate" | "high" | "very_high" | "unknown";
  };
}

export interface ModelMetrics {
  model_version: string;
  prediction_mode: string;
  weights: Record<string, number>;
  inverted_features: string[];
  classification_thresholds: Record<string, [number, number]>;
  methodology_source: string;
  feature_summary: Record<string, any>;
  class_distribution: Record<string, number>;
  fsi_mean?: number;
  fsi_std?: number;
  supervised_ml: {
    status: string;
    reason: string;
    minimum_requirements_for_ml: string;
  };
}
