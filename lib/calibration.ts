import { QuantileValidationMetric } from './types';

export const PREDECLARED_CALIBRATION_TOLERANCE = 0.03;

export interface CalibrationDecision {
  tolerance: number;
  passedQuantiles: QuantileValidationMetric['quantile'][];
  failedQuantiles: QuantileValidationMetric['quantile'][];
  allPassed: boolean;
}

export function evaluateCalibrationTolerance(
  metrics: QuantileValidationMetric[],
  tolerance: number,
): CalibrationDecision {
  if (!Number.isFinite(tolerance) || tolerance < 0) {
    throw new RangeError('Calibration tolerance must be a non-negative finite number.');
  }

  const passedQuantiles = metrics
    .filter((metric) => metric.absolute_coverage_error <= tolerance)
    .map((metric) => metric.quantile);
  const failedQuantiles = metrics
    .filter((metric) => metric.absolute_coverage_error > tolerance)
    .map((metric) => metric.quantile);

  return {
    tolerance,
    passedQuantiles,
    failedQuantiles,
    allPassed: failedQuantiles.length === 0,
  };
}
