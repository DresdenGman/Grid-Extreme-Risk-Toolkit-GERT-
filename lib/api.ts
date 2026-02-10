import { PredictRequest, PredictionOut, ScenarioRequest, ScenarioResponse, BacktestResponse, AIAnalysisResponse, WeatherFeatures, EventPlaybackResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
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
      baseline_p99: base + 4000, // Flat envelope
      gert_p99: base + (isSpike ? 18000 : 6000) // Reactive envelope
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

// --- FETCH WRAPPER WITH FALLBACK ---

async function fetchJson<T>(endpoint: string, options: RequestInit, mockData: T): Promise<T> {
  try {
    // Set a short timeout for the demo so it falls back quickly if backend is missing
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000); // Increased timeout for AI
    
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
      throw new Error(`API status: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.warn(`Backend unreachable (${endpoint}), using Mock Data for preview.`, error);
    // In production, you might want to throw. For this Preview MVP, we return mock data.
    return Promise.resolve(mockData);
  }
}

export const api = {
  predict: (data: PredictRequest) => 
    fetchJson<PredictionOut>('/predict', { method: 'POST', body: JSON.stringify(data) }, MOCK_PREDICTION),
  
  scenario: (data: ScenarioRequest) => 
    fetchJson<ScenarioResponse>('/scenario', { method: 'POST', body: JSON.stringify(data) }, MOCK_SCENARIO),

  analyze: (data: PredictRequest) =>
    fetchJson<AIAnalysisResponse>('/analyze', { method: 'POST', body: JSON.stringify(data) }, MOCK_ANALYSIS),

  liveWeather: (region: string) => 
    fetchJson<WeatherFeatures>(`/weather/live?region=${region}`, { method: 'GET' }, MOCK_WEATHER),

  backtest: () =>
    fetchJson<BacktestResponse>('/backtest', { method: 'GET' }, MOCK_BACKTEST),
    
  health: () => fetchJson<{status: string}>('/health', { method: 'GET' }, { status: 'mock-ok' }),

  fetchEventPlayback: (id: string) =>
    fetchJson<EventPlaybackResponse>(`/events/playback/${id}`, { method: 'GET' }, {
      event_id: 'mock',
      title: 'Mock Event',
      total_hours: 24,
      steps: [],
      logs: []
    })
};