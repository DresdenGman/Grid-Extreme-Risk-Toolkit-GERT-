
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';

export type Region = 'ERCOT_NORTH' | 'CAISO' | 'PJM' | 'NYISO';

export interface WeatherFeatures {
  temperature: number;
  wind_speed: number;
  solar_irradiance: number;
}

export interface PredictRequest {
  region: string;
  date: string;
  weather_features: WeatherFeatures;
}

export interface Diagnostics {
  input_region: string;
  model_version: string;
  backend_type: string;
  capacity_used?: number;
  data_source?: 'real_time' | 'simulated';
  real_load_mw?: number;
  real_capacity_mw?: number;
}

export interface FinancialImpact {
  eue_mwh: number;        // Expected Unserved Energy
  voll_price: number;     // Value of Lost Load ($/MWh)
  estimated_loss: number; // Total estimated economic loss
}

export interface PredictionOut {
  timestamp: string;
  q50_load_mw: number;
  q90_load_mw: number;
  q95_load_mw: number;
  q99_load_mw: number;
  risk_level: RiskLevel;
  risk_score: number;
  financial?: FinancialImpact; // New field
  diagnostics: Diagnostics;
}

export interface ScenarioRequest {
  baseline_request: PredictRequest;
  perturbations: Partial<Record<keyof WeatherFeatures, number>>;
}

export interface ScenarioResponse {
  scenario_id: string;
  baseline_risk_score: number;
  scenario_risk_score: number;
  risk_delta: number;
  reserve_shortfall_mw: number; // New: How much generation is missing?
  financial_impact: FinancialImpact; // New: Cost of the scenario
  new_prediction: PredictionOut;
}

export interface BacktestPoint {
  hour: number;
  actual_load: number;
  baseline_p99: number;
  gert_p99: number;
}

export interface CalibrationBin {
  prob_bucket: string; // e.g., "0-10%", "90-100%"
  observed_freq: number; // Actual percentage of points falling in this bucket
  ideal_freq: number;    // Ideal percentage
}

export interface ModelMetrics {
  model_name: string;
  coverage_p99: number;
  pinball_loss: number;
  description: string;
}

export interface BacktestResponse {
  time_series: BacktestPoint[];
  metrics: ModelMetrics[];
  calibration_curve: CalibrationBin[]; // New: Reliability Diagram Data
}

// --- AI Analysis Types ---

export interface AIDriver {
  factor: string;
  direction: string;
  evidence: string;
}

export interface AIActions {
  operator: string[];
  public: string[];
}

export interface AIAnalysisResponse {
  headline: string;
  drivers: AIDriver[];
  uncertainty: string;
  actions: AIActions;
  confidence: string;
}

// --- Event Playback Types ---

export interface EventLog {
  hour: number;
  message: string;
  source: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
}

export interface EventStep {
  hour: number;
  timestamp_label: string;
  temperature: number;
  actual_load_mw: number;
  capacity_mw: number;
  gert_p99_load_mw: number;
  risk_score: number;
}

export interface EventPlaybackResponse {
  event_id: string;
  title: string;
  total_hours: number;
  steps: EventStep[];
  logs: EventLog[];
}

export interface GridLoadResponse {
  region: string;
  current_load_mw: number;
  capacity_mw: number;
  utilization_percent: number;
  timestamp: string;
  data_source: 'real_time' | 'simulated';
}

export interface HealthStatus {
  status: string;
  backend: string;
  ai_enabled: boolean;
  env: string;
}