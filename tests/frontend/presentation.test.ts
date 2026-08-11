import { describe, expect, it } from 'vitest';
import {
  createPresentationPrediction,
  createPresentationPrior,
  PRESENTATION_WEATHER,
} from '../../lib/presentation';

describe('presentation snapshot', () => {
  it('keeps quantiles ordered and capacity context explicit', () => {
    const result = createPresentationPrediction();

    expect(result.q50_load_mw).toBeLessThan(result.q90_load_mw);
    expect(result.q90_load_mw).toBeLessThan(result.q95_load_mw);
    expect(result.q95_load_mw).toBeLessThan(result.q99_load_mw);
    expect(result.q99_load_mw).toBeLessThan(result.diagnostics.capacity_used!);
    expect(result.diagnostics.backend_type).toBe('presentation_demo');
  });

  it('responds deterministically to a hotter stress scenario', () => {
    const baseline = createPresentationPrediction();
    const hotter = createPresentationPrediction({
      ...PRESENTATION_WEATHER,
      temperature: PRESENTATION_WEATHER.temperature + 2,
    });

    expect(hotter.q99_load_mw).toBeGreaterThan(baseline.q99_load_mw);
    expect(hotter.risk_score).toBeGreaterThan(baseline.risk_score);
    expect(createPresentationPrior().risk_score).toBeLessThan(baseline.risk_score);
  });
});
