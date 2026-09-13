import bundle from '@/public/data/historical-cases.json';

export const historicalCases = bundle.cases;
export const historicalSource = bundle;
export type HistoricalCase = (typeof historicalCases)[number];
export const ANALYSIS_VERSION = 'historical-capacity-v1';
export const REPO_URL = 'https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-';

export function analyzeHistory(example: HistoricalCase, capacityMw: number, reductionPercent: number) {
  if (!Number.isFinite(capacityMw) || capacityMw < 10000 || capacityMw > 120000) {
    throw new RangeError('Capacity must be between 10,000 and 120,000 MW.');
  }
  if (!Number.isFinite(reductionPercent) || reductionPercent < 0 || reductionPercent > 20) {
    throw new RangeError('Load reduction must be between 0 and 20 percent.');
  }
  const rows = example.hours.map((hour) => {
    const adjustedLoadMw = hour.load_mw * (1 - reductionPercent / 100);
    return {
      timestamp: hour.timestamp,
      recordedLoadMw: hour.load_mw,
      adjustedLoadMw,
      assumedCapacityMw: capacityMw,
      originalGapMw: Math.max(0, hour.load_mw - capacityMw),
      adjustedGapMw: Math.max(0, adjustedLoadMw - capacityMw),
    };
  });
  const originalGapMwh = rows.reduce((sum, row) => sum + row.originalGapMw, 0);
  const adjustedGapMwh = rows.reduce((sum, row) => sum + row.adjustedGapMw, 0);
  return {
    rows,
    recordedPeakMw: Math.max(...rows.map((row) => row.recordedLoadMw)),
    adjustedPeakMw: Math.max(...rows.map((row) => row.adjustedLoadMw)),
    originalHoursAboveCapacity: rows.filter((row) => row.originalGapMw > 0).length,
    adjustedHoursAboveCapacity: rows.filter((row) => row.adjustedGapMw > 0).length,
    originalGapMwh,
    adjustedGapMwh,
    avoidedGapMwh: originalGapMwh - adjustedGapMwh,
    minimumUniformReductionPercent: Math.max(0, 100 * (1 - capacityMw / Math.max(...rows.map((row) => row.recordedLoadMw)))),
  };
}

export function analysisReport(example: HistoricalCase, capacityMw: number, reductionPercent: number) {
  const { rows, ...metrics } = analyzeHistory(example, capacityMw, reductionPercent);
  return {
    schema: 'gert-historical-report-v1',
    analysis_version: ANALYSIS_VERSION,
    dataset_version: bundle.version,
    case_id: example.id,
    source_url: example.source_url,
    source_archive_sha256: example.source_archive_sha256,
    timezone: bundle.timezone,
    timestamp_convention: bundle.timestamp_convention,
    load_definition: bundle.load_definition,
    assumptions: { capacity_mw: capacityMw, uniform_load_reduction_percent: reductionPercent, interval_hours: 1 },
    methodology: 'adjusted_load = recorded_load * (1 - reduction_percent / 100); gap_MWh = sum(max(0, load_MW - assumed_capacity_MW) * 1 hour).',
    limitations: [
      'Capacity and load reduction are user assumptions, not observed historical capacity or realized intervention.',
      'Gap energy is a deterministic counterfactual; it is not expected unserved energy, a forecast, an outage estimate, or proof of savings.',
      'Aggregate load alone cannot establish reliability: generation, network constraints, reserves, and operational feasibility are not modeled.',
      'The minimum reduction is an algebraic requirement under these assumptions, not an operational recommendation.',
      example.note,
    ],
    metrics,
    rows,
  };
}

export function reportCsv(report: ReturnType<typeof analysisReport>) {
  // Fixed keys and numeric values only; no user-provided spreadsheet formulas.
  const headers = ['interval_start', 'recorded_load_mw', 'adjusted_load_mw', 'assumed_capacity_mw', 'original_gap_mw', 'adjusted_gap_mw'];
  return [headers.join(','), ...report.rows.map((row) => [
    row.timestamp, row.recordedLoadMw, row.adjustedLoadMw.toFixed(3), row.assumedCapacityMw,
    row.originalGapMw.toFixed(3), row.adjustedGapMw.toFixed(3),
  ].join(','))].join('\n') + '\n';
}
