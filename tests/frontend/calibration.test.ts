import { describe, expect, it } from 'vitest';
import {
  evaluateCalibrationTolerance,
  formatPinballSkill,
  PREDECLARED_CALIBRATION_TOLERANCE,
} from '../../lib/calibration';
import evidence from '../../evidence/ercot_v1_4_validation.json';
import { QuantileValidationMetric } from '../../lib/types';

const metrics = evidence.quantile_metrics as QuantileValidationMetric[];

describe('calibration evidence rehearsal', () => {
  it('reproduces the published 1-of-4 calibration decision at 3 pp', () => {
    const result = evaluateCalibrationTolerance(metrics, PREDECLARED_CALIBRATION_TOLERANCE);

    expect(result.passedQuantiles).toEqual(['q50']);
    expect(result.failedQuantiles).toEqual(['q90', 'q95', 'q99']);
    expect(result.allPassed).toBe(false);
  });

  it('shows that a 4.5 pp hypothetical tolerance would pass every quantile', () => {
    const result = evaluateCalibrationTolerance(metrics, 0.045);

    expect(result.failedQuantiles).toEqual([]);
    expect(result.allPassed).toBe(true);
  });

  it('writes the minimum pinball skill as +0.76', () => {
    const minimum = Math.min(...metrics.map((metric) => metric.pinball_skill_vs_baseline));
    expect(formatPinballSkill(minimum)).toBe('+0.76');
    expect(formatPinballSkill(0.841492)).toBe('+0.84');
    expect(formatPinballSkill(minimum)).not.toContain('%');
  });

  it('rejects invalid tolerances rather than producing a misleading decision', () => {
    expect(() => evaluateCalibrationTolerance(metrics, -0.01)).toThrow(RangeError);
    expect(() => evaluateCalibrationTolerance(metrics, Number.NaN)).toThrow(RangeError);
  });
});
