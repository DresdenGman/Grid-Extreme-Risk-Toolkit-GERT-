import {
  PredictRequest, PredictionOut, ScenarioRequest, ScenarioResponse,
  BacktestResponse, AIAnalysisResponse, WeatherFeatures,
  EventPlaybackResponse, HealthStatus, GridLoadResponse,
  ApiClientError, ApiErrorKind, DataMode, DataEnvelope, Provenance
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getDataMode(): DataMode {
  const raw = process.env.NEXT_PUBLIC_DATA_MODE;
  if (raw === 'live') return 'live';
  if (raw === 'demo') return 'demo';
  if (raw !== undefined) {
    console.warn(`Invalid NEXT_PUBLIC_DATA_MODE="${raw}". Treating as "live".`);
  }
  return 'live';
}

// --- MOCK DATA FOR DEMO MODE ---

const MOCK_PREDICTION: PredictionOut = {
  timestamp: new Date().toISOString(),
  q50_load_mw: 42500,
  q90_load_mw: 48000,
  q95_load_mw: 51000,
  q99_load_mw: 56500,
  risk_level: "EXTREME",
  risk_score: 92.5,
  financial: {
    eue_mwh: 1500,
    voll_price: 9000,
    estimated_loss: 13500000
  },
  diagnostics: {
    input_region: "MOCK_DEMO",
    model_version: "demo-v1",
    backend_type: "frontend-fallback",
    capacity_used: 55000
  }
};

const MOCK_SCENARIO: ScenarioResponse = {
  scenario_id: "sim_mock_123",
  baseline_risk_score: 45.0,
  scenario_risk_score: 92.5,
  risk_delta: 47.5,
  reserve_shortfall_mw: 1500,
  financial_impact: {
      eue_mwh: 1500,
      voll_price: 9000,
      estimated_loss: 13500000
  },
  new_prediction: MOCK_PREDICTION
};

const MOCK_BACKTEST: BacktestResponse = {
  time_series: Array.from({ length: 72 }, (_, i) => {
    const base = 40000 + 5000 * Math.sin(i / 24 * 2 * Math.PI);
    const isSpike = i === 20 || i === 50;
    const spike = isSpike ? 15000 : 0;
    const actual = base + spike + (Math.random() * 1000 - 500);
    return {
      hour: i,
      actual_load: actual,
      baseline_p99: base + 4000,
      gert_p99: base + (isSpike ? 18000 : 6000)
    };
  }),
  metrics: [
    {
      model_name: "Baseline (Mean/OLS)",
      coverage_p99: 85.2,
      pinball_loss: 450.5,
      description: "Standard regression. Fails to capture tail risk."
    },
    {
      model_name: "GERT (Quantile)",
      coverage_p99: 99.1,
      pinball_loss: 120.3,
      description: "Adapts to volatility. High coverage."
    }
  ],
  calibration_curve: [
      { prob_bucket: "0-50%", observed_freq: 0.48, ideal_freq: 0.50 },
      { prob_bucket: "50-90%", observed_freq: 0.89, ideal_freq: 0.90 },
      { prob_bucket: "90-95%", observed_freq: 0.94, ideal_freq: 0.95 },
      { prob_bucket: "95-99%", observed_freq: 0.985, ideal_freq: 0.99 },
      { prob_bucket: ">99%", observed_freq: 0.996, ideal_freq: 0.999 },
  ]
};

const MOCK_ANALYSIS: AIAnalysisResponse = {
  headline: "EXTREME Risk: P99 Load Exceeds Capacity by 1.5GW",
  drivers: [
    { factor: "Temperature", direction: "Increase", evidence: "Low temperature (-5C) driving heating demand" },
    { factor: "Wind Volatility", direction: "Uncertainty", evidence: "High wind variance widens P99-P50 gap" }
  ],
  uncertainty: "Wind generation reliability is the primary uncertainty factor.",
  actions: {
    operator: ["Activate contingency reserves", "Prepare for load shedding"],
    public: ["Reduce heating setpoints", "Avoid major appliances"]
  },
  confidence: "HIGH"
};

const MOCK_WEATHER: WeatherFeatures = {
    temperature: 25.0,
    wind_speed: 10.0,
    solar_irradiance: 800.0
};

// --- DEMO MODE: return mock data with envelope ---

function demoEnvelope<T>(data: T): DataEnvelope<T> {
  return {
    data,
    source: 'simulated_demo',
    fetchedAt: new Date().toISOString(),
  };
}

// --- LIVE MODE: fetch with typed error classification ---

function classifyError(error: unknown, endpoint: string): ApiClientError {
  if (error instanceof ApiClientError) return error;

  const message = error instanceof Error ? error.message : String(error);
  const name = error instanceof Error ? error.name : '';

  if (name === 'AbortError') {
    return new ApiClientError(
      `Request to ${endpoint} timed out after 8 seconds.`,
      'timeout'
    );
  }

  // Check for HTTP status embedded in message
  const statusMatch = message.match(/API Error \((\d+)\)/);
  if (statusMatch) {
    const status = parseInt(statusMatch[1]);
    if (status === 429) {
      return new ApiClientError(
        `Prediction service is rate-limited. Try again later.`,
        'rate_limit',
        { status }
      );
    }
    return new ApiClientError(
      `Prediction service returned an error (${status}).`,
      'http',
      { status }
    );
  }

  if (message.includes('Failed to fetch') || message.includes('fetch failed') || message.includes('NetworkError')) {
    return new ApiClientError(
      'Cannot reach the prediction service.',
      'network'
    );
  }

  return new ApiClientError(
    `Unexpected error from ${endpoint}: ${message}`,
    'network'
  );
}

async function liveFetch<T>(
  endpoint: string,
  options: RequestInit,
): Promise<DataEnvelope<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let detail = `API Error (${res.status})`;
      try {
        const errorJson = await res.text().then(t => JSON.parse(t));
        detail = errorJson.detail || detail;
      } catch { /* use default */ }
      throw new ApiClientError(
        detail,
        res.status === 429 ? 'rate_limit' : 'http',
        { status: res.status }
      );
    }

    const data: T = await res.json();
    return {
      data,
      source: 'live_api' as Provenance,
      fetchedAt: new Date().toISOString(),
    };
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    throw classifyError(error, endpoint);
  }
}

// --- PUBLIC API ---

export const api = {
  predict: (data: PredictRequest): Promise<DataEnvelope<PredictionOut>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope(MOCK_PREDICTION))
      : liveFetch<PredictionOut>('/predict', { method: 'POST', body: JSON.stringify(data) }),

  scenario: (data: ScenarioRequest): Promise<DataEnvelope<ScenarioResponse>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope(MOCK_SCENARIO))
      : liveFetch<ScenarioResponse>('/scenario', { method: 'POST', body: JSON.stringify(data) }),

  analyze: (data: PredictRequest): Promise<DataEnvelope<AIAnalysisResponse>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope(MOCK_ANALYSIS))
      : liveFetch<AIAnalysisResponse>('/analyze', { method: 'POST', body: JSON.stringify(data) }),

  liveWeather: (region: string): Promise<DataEnvelope<WeatherFeatures>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope(MOCK_WEATHER))
      : liveFetch<WeatherFeatures>(`/weather/live?region=${region}`, { method: 'GET' }),

  backtest: (): Promise<DataEnvelope<BacktestResponse>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope(MOCK_BACKTEST))
      : liveFetch<BacktestResponse>('/backtest', { method: 'GET' }),

  health: async (): Promise<DataEnvelope<HealthStatus>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope({
          status: 'mock-ok',
          backend: 'stub-v1',
          ai_enabled: false,
          env: 'dev'
        }))
      : liveFetch<HealthStatus>('/health', { method: 'GET' }),

  fetchEventPlayback: (id: string): Promise<DataEnvelope<EventPlaybackResponse>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope({
          event_id: 'mock',
          title: 'Mock Event',
          total_hours: 24,
          steps: [],
          logs: []
        }))
      : liveFetch<EventPlaybackResponse>(`/events/playback/${id}`, { method: 'GET' }),

  getCurrentLoad: (region: string): Promise<DataEnvelope<GridLoadResponse>> =>
    getDataMode() === 'demo'
      ? Promise.resolve(demoEnvelope({
          region,
          current_load_mw: 45000,
          capacity_mw: 65000,
          utilization_percent: 69.2,
          timestamp: new Date().toISOString(),
          data_source: 'estimated_fallback',
          capacity_source: 'configured_reference',
          capacity_basis: 'configured regional reference'
        }))
      : liveFetch<GridLoadResponse>(`/load/current?region=${region}`, { method: 'GET' }),
};
