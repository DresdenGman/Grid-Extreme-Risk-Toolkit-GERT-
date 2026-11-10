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
    const v14 = execSync('git log -1 --format=%H -- evidence/ercot_v1_4_validation.json', { encoding: 'utf8' }).trim();
    const prereg = execSync('git rev-parse 2fcf2c9b', { encoding: 'utf8' }).trim();
    const dated = execSync('git log -1 --format=%ci 2fcf2c9b', { encoding: 'utf8' }).trim();
    expect(v14).toBe('4cb93a8e4117251ad8c9248d1eaf3643a7c33c2f');
    expect(prereg.startsWith('2fcf2c9b')).toBe(true);
    expect(dated.startsWith('2026-11-05 03:11:19 -0800')).toBe(true);
    const raw = readFileSync('evidence/snapshots/pr-23/ercot_v1_5_validation.json', 'utf8');
    expect(raw).toContain('timestamps before 2025-01-01');
    expect(raw).toContain('realized ERA5');
  });
});
