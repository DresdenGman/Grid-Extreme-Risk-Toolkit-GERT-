
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';

export type Region = 'ERCOT_SYSTEM' | 'CAISO' | 'PJM' | 'NYISO';

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
  /** Source of the grid-load context. It is distinct from the model itself. */
  load_data_source?: 'official_live' | 'estimated_fallback';
  capacity_data_source?: 'official_adequacy' | 'configured_reference';
  capacity_basis?: string;
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
  provenance: 'verified_observation' | 'synthetic_reconstruction';
  methodology_note: string;
}

export interface GridLoadResponse {
  region: string;
  current_load_mw: number;
  capacity_mw: number;
  utilization_percent: number;
  timestamp: string;
  data_source: 'official_live' | 'estimated_fallback';
  capacity_source: 'official_adequacy' | 'configured_reference';
  capacity_basis: string;
}

export interface HealthStatus {
  status: string;
  backend: string;
  ai_enabled: boolean;
  env: string;
}

export interface ProductStatus {
  status: 'operational' | 'degraded';
  environment: string;
  model_status: 'validated_production' | 'provisional_candidate' | 'rejected_candidate' | 'demonstration_stub';
  model_version: string;
  capabilities: {
    official_ercot_data: boolean;
    probabilistic_prediction: boolean;
    scenario_analysis: boolean;
    validated_backtest: boolean;
    ai_analysis: boolean;
    presentation_mode: boolean;
  };
}

export interface QuantileValidationMetric {
  quantile: 'q50' | 'q90' | 'q95' | 'q99';
  target_coverage: number;
  empirical_coverage: number;
  absolute_coverage_error: number;
  pinball_skill_vs_baseline: number;
}

export interface ValidationGate {
  gate: string;
  passed: boolean;
  observed: number;
  requirement: string;
}

export interface ModelEvidence {
  candidate_id: string;
  validation_status: 'validated_production' | 'provisional_candidate' | 'rejected_candidate';
  summary: string;
  evaluation_window_start: string;
  evaluation_window_end: string;
  observations: number;
  q50_mae_mw: number;
  quantile_crossings: number;
  quantile_metrics: QuantileValidationMetric[];
  gates: ValidationGate[];
  all_gates_passed: boolean;
  data_provenance: string;
  limitations: string[];
  published_at: string;
}

// --- Data Provenance ---

export type DataMode = 'live' | 'demo';

export type Provenance = 'live_api' | 'simulated_demo' | 'versioned_release_evidence';

export interface DataEnvelope<T> {
  data: T;
  source: Provenance;
  fetchedAt: string;
}

// --- API Error Types ---

export type ApiErrorKind =
  | 'timeout'
  | 'rate_limit'
  | 'http'
  | 'network'
  | 'invalid_response'
  | 'configuration';

export class ApiClientError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly retryAfterSeconds?: number;

  constructor(
    message: string,
    kind: ApiErrorKind,
    options?: {
      status?: number;
      retryAfterSeconds?: number;
      cause?: unknown;
    },
  ) {
    super(message, { cause: options?.cause });
    this.name = 'ApiClientError';
    this.kind = kind;
    this.status = options?.status;
    this.retryAfterSeconds = options?.retryAfterSeconds;
  }
}
