import { describe, expect, it } from 'vitest';
import { analyzeHistory, analysisReport, historicalCases, reportCsv } from '../../lib/historical';

describe('historical capacity analysis', () => {
  it('integrates hourly power gaps into energy with a hand-worked two-hour example', () => {
    const example = { ...historicalCases[0], hours: [
      { timestamp: '2023-08-09T00:00:00-05:00', load_mw: 12000 },
      { timestamp: '2023-08-09T01:00:00-05:00', load_mw: 18000 },
    ] };
    const result = analyzeHistory(example, 15000, 10);
    expect(result.originalGapMwh).toBe(3000);
    expect(result.adjustedGapMwh).toBe(1200);
    expect(result.avoidedGapMwh).toBe(1800);
    expect(result.adjustedHoursAboveCapacity).toBe(1);
    expect(result.minimumUniformReductionPercent).toBeCloseTo(100 / 6);
  });

  it('uses 72 contiguous finite observed hours in each of three source-linked cases', () => {
    expect(historicalCases).toHaveLength(3);
    for (const example of historicalCases) {
      expect(example.hours).toHaveLength(72);
      expect(example.source_archive_sha256).toMatch(/^[a-f0-9]{64}$/);
      expect(example.source_url.startsWith('https://www.ercot.com/')).toBe(true);
      example.hours.forEach((hour, i) => {
        expect(Number.isFinite(hour.load_mw) && hour.load_mw > 0).toBe(true);
        if (i) expect(Date.parse(hour.timestamp) - Date.parse(example.hours[i - 1].timestamp)).toBe(3600000);
      });
    }
  });

  it('does not invent benefits at zero reduction or when capacity already covers every observation', () => {
    for (const example of historicalCases) {
      expect(analyzeHistory(example, example.default_capacity_mw, 0).avoidedGapMwh).toBe(0);
      expect(analyzeHistory(example, 120000, 5).originalGapMwh).toBe(0);
      expect(analyzeHistory(example, 120000, 5).minimumUniformReductionPercent).toBe(0);
    }
  });

  it('gap and exceedance hours cannot grow when reduction or capacity increases', () => {
    for (const example of historicalCases) {
      for (const capacity of [30000, 60000, 90000]) {
        const low = analyzeHistory(example, capacity, 0);
        const high = analyzeHistory(example, capacity, 10);
        expect(high.adjustedGapMwh).toBeLessThanOrEqual(low.adjustedGapMwh);
        expect(high.adjustedHoursAboveCapacity).toBeLessThanOrEqual(low.adjustedHoursAboveCapacity);
        expect(analyzeHistory(example, capacity + 10000, 10).adjustedGapMwh).toBeLessThanOrEqual(high.adjustedGapMwh);
      }
    }
  });

  it('rejects NaN, infinity, and assumptions outside supported ranges', () => {
    for (const capacity of [NaN, Infinity, 0, 120001]) expect(() => analyzeHistory(historicalCases[0], capacity, 5)).toThrow(RangeError);
    for (const reduction of [NaN, Infinity, -1, 21]) expect(() => analyzeHistory(historicalCases[0], 80000, reduction)).toThrow(RangeError);
  });

  it('exports all rows and explicit assumptions, source hash, formulas, and limitations', () => {
    const report = analysisReport(historicalCases[0], 80000, 5);
    expect(report.assumptions).toEqual({ capacity_mw: 80000, uniform_load_reduction_percent: 5, interval_hours: 1 });
    expect(report.rows).toHaveLength(72);
    expect(report.limitations.join(' ')).toContain('not expected unserved energy');
    expect(reportCsv(report).trim().split('\n')).toHaveLength(73);
    expect(report.source_archive_sha256).toBe(historicalCases[0].source_archive_sha256);
  });
});
