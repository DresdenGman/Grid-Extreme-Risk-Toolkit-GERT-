import { PredictionOut, RiskLevel, WeatherFeatures } from '@/lib/types';

export const PRESENTATION_WEATHER: WeatherFeatures = {
  temperature: 41.2,
  wind_speed: 5.8,
  solar_irradiance: 690,
};

const CAPACITY_MW = 82_500;

function riskLevel(score: number): RiskLevel {
  if (score >= 90) return 'EXTREME';
  if (score >= 70) return 'HIGH';
  if (score >= 40) return 'MODERATE';
  return 'LOW';
}

/**
 * A deterministic, internally consistent snapshot for product presentations.
 * It never leaves the browser and is deliberately identified as simulated data.
 */
export function createPresentationPrediction(
  weather: WeatherFeatures = PRESENTATION_WEATHER,
): PredictionOut {
  const weatherShift =
    (weather.temperature - PRESENTATION_WEATHER.temperature) * 230
    - (weather.wind_speed - PRESENTATION_WEATHER.wind_speed) * 70
    + (weather.solar_irradiance - PRESENTATION_WEATHER.solar_irradiance) * 0.35;
  const q50 = 75_400 + weatherShift;
  const tailPressure = Math.max(0, weather.temperature - 38) * 145
    + Math.max(0, 8 - weather.wind_speed) * 90;
  const q90 = q50 + 3_600 + tailPressure * 0.28;
  const q95 = q50 + 4_800 + tailPressure * 0.48;
  const q99 = q50 + 5_900 + tailPressure * 0.72;
  const riskScore = Math.max(0, Math.min(100, 84.6 + weatherShift / 360 + (q99 - 81_300) / 520));

  return {
    timestamp: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    q50_load_mw: Math.round(q50),
    q90_load_mw: Math.round(q90),
    q95_load_mw: Math.round(q95),
    q99_load_mw: Math.round(q99),
    risk_level: riskLevel(riskScore),
    risk_score: Number(riskScore.toFixed(1)),
    financial: {
      eue_mwh: 0,
      voll_price: 9_000,
      estimated_loss: 0,
    },
    diagnostics: {
      input_region: 'ERCOT_SYSTEM',
      model_version: 'gert-tail-qrf.presentation',
      backend_type: 'presentation_demo',
      capacity_used: CAPACITY_MW,
      load_data_source: 'estimated_fallback',
      capacity_data_source: 'configured_reference',
      capacity_basis: 'Simulated ERCOT peak-day adequacy snapshot',
      real_load_mw: Math.round(q50 - 580),
      real_capacity_mw: CAPACITY_MW,
    },
  };
}

export function createPresentationPrior(): PredictionOut {
  const current = createPresentationPrediction();
  return {
    ...current,
    q50_load_mw: current.q50_load_mw - 1_050,
    q90_load_mw: current.q90_load_mw - 900,
    q95_load_mw: current.q95_load_mw - 760,
    q99_load_mw: current.q99_load_mw - 610,
    risk_level: 'HIGH',
    risk_score: 77.8,
  };
}
