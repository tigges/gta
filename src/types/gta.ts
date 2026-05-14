// Shared TypeScript types for GTA data models

export interface Trailer {
  youtube_id: string;
  title: string;
  published_at: string | null;
  source_url: string;
}

export interface TrailersData {
  last_updated: string;
  source: string;
  trailers: Trailer[];
}

export interface PredictionRange {
  low: string;
  high: string;
}

export interface Prediction {
  id: string;
  title: string;
  value: string;
  unit: string | null;
  confidence: number;
  confidence_tier: "confirmed" | "reported" | "predicted";
  basis: string;
  trailer_timestamp: string | null;
  prediction_method: string | null;
  prediction_inputs: string[];
  prediction_range: PredictionRange | null;
  outcome_verified: boolean;
  outcome_actual: string | null;
  outcome_date: string | null;
  source: string;
  source_type: "official" | "reported" | "predicted";
}

export interface PredictionsData {
  last_updated: string;
  note: string;
  schema_version: string;
  predictions: Prediction[];
}
