import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { buildFigure } from '../../lib/homepage/figure';
import { loadEvidence } from '../../lib/homepage/evidence';

describe('fig1 reproduction command', () => {
  it('prints the same coverage series the homepage plots', () => {
    const printed = JSON.parse(execSync('node scripts/fig1.mjs', { encoding: 'utf8' }));
    const evidence = loadEvidence();
    const figure = buildFigure(evidence);
    expect(printed.v14.map((row: { absolute_coverage_error: number }) => row.absolute_coverage_error))
      .toEqual(evidence.v14.points.map((point) => point.absoluteError));
    expect(printed.v15.map((row: { absolute_coverage_error: number }) => row.absolute_coverage_error))
      .toEqual(evidence.v15?.points.map((point) => point.absoluteError));
    expect(printed.v14.every((row: { wilson_95: unknown }) => row.wilson_95 === null)).toBe(true);
    expect(printed.v15.every((row: { wilson_95: number[] }) => Array.isArray(row.wilson_95))).toBe(true);
    expect(figure.columns[0].v14.signed.endsWith(String(evidence.v14.points[0].absoluteError))).toBe(true);
  });

  it('pins the evidence commits that the pages name', () => {
    const v14 = execSync('git hash-object evidence/ercot_v1_4_validation.json', { encoding: 'utf8' }).trim();
    expect(v14).toBe('c36a8722c8155c0eec55ed1a21570b897f08bb00');
    const prereg = readFileSync('docs/PREREGISTRATION_ERCOT_v1_5.md', 'utf8');
    expect(prereg).toContain('2026-11-01');
    expect(prereg).toContain('timestamps < 2025-01-01');
    const raw = readFileSync('evidence/snapshots/pr-23/ercot_v1_5_validation.json', 'utf8');
    expect(raw).toContain('timestamps before 2025-01-01');
    expect(raw).toContain('realized ERA5');
    expect(raw).toContain('2026-11-01T23:00:00Z');
  });
});
