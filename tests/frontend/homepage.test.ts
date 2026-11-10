import { createHash } from 'crypto';
import { readdirSync, readFileSync } from 'fs';
import path from 'path';
import { describe, expect, it } from 'vitest';
import { buildCopy, spanText } from '../../lib/homepage/copy';
import { loadCitation } from '../../lib/homepage/citation';
import { V15_PR23_SNAPSHOT, loadEvidence } from '../../lib/homepage/evidence';
import { buildFigure } from '../../lib/homepage/figure';
import { formatPlain } from '../../lib/homepage/format';
import { UNAVAILABLE, interpretLive } from '../../lib/homepage/live';
import { toolEntries, toolHrefs } from '../../lib/homepage/tools';
import { PREDECLARED_CALIBRATION_TOLERANCE } from '../../lib/calibration';

const evidence = loadEvidence();
const citation = loadCitation();
const copy = buildCopy(evidence, citation);
const figure = buildFigure(evidence);

describe('homepage evidence', () => {
  it('pins the PR #23 snapshot to the upstream blob', () => {
    const bytes = readFileSync(path.join(process.cwd(), V15_PR23_SNAPSHOT.localPath));
    const hash = createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
    expect(hash).toBe(V15_PR23_SNAPSHOT.blobSha1);
    expect(evidence.v15?.source).toMatchObject({
      kind: 'pr23-snapshot',
      pr: 23,
      commit: V15_PR23_SNAPSHOT.commit,
    });
  });

  it('reads the gate and both candidates from the evidence files', () => {
    expect(evidence.tolerance).toBe(PREDECLARED_CALIBRATION_TOLERANCE);
    expect(evidence.gateLabel).toBe('0.03');
    expect(evidence.productionValidated).toBe(false);
    expect(evidence.v14.status).toBe('rejected_candidate');
    expect(evidence.v14.allGatesPassed).toBe(false);
    expect(evidence.v14.failedLabels).toEqual(['Q90', 'Q95', 'Q99']);
    expect(evidence.v14.passedLabels).toEqual(['Q50']);
    expect(evidence.v14.points.every((point) => point.wilson === null)).toBe(true);
    expect(evidence.v15?.status).toBe('provisional_candidate');
    expect(evidence.v15?.allGatesPassed).toBe(true);
    expect(evidence.v15?.failedLabels).toEqual([]);
    expect(evidence.v15?.wilsonComplete).toBe(true);
  });

  it('spells published coverage digits and only marks intervals that leave the band', () => {
    const raw14 = readFileSync(path.join(process.cwd(), 'evidence/ercot_v1_4_validation.json'), 'utf8');
    const raw15 = readFileSync(path.join(process.cwd(), V15_PR23_SNAPSHOT.localPath), 'utf8');
    for (const point of evidence.v14.points) {
      expect(raw14).toContain(String(point.empirical));
      expect(formatPlain(point.absoluteError)).toBe(String(point.absoluteError));
      expect(Math.sign(point.signedError)).toBe(Math.sign(point.empirical - point.nominal));
    }
    expect(evidence.v15).not.toBeNull();
    for (const point of evidence.v15!.points) {
      expect(raw15).toContain(String(point.empirical));
      expect(point.wilson).not.toBeNull();
      expect(formatPlain(point.wilson![0])).toBe(String(point.wilson![0]));
    }
    expect(evidence.v15!.points.filter((point) => point.intervalPastGate).map((point) => point.label)).toEqual([
      'Q50',
      'Q90',
    ]);
  });

  it('keeps v1.5 provisional and unmerged in the page copy', () => {
    const text = spanText(copy.dek);
    expect(copy.subhead).toBe('No validated production model.');
    expect(copy.verdicts.map((item) => item.value)).toEqual(['None.', 'Rejected.', 'Provisional.']);
    expect(copy.aside).toBe('PR #23, unmerged. Realized ERA5, not in production.');
    expect(text).toContain('passed the gates recorded in its evidence JSON and remains provisional');
    expect(text).toContain('unmerged');
    expect(text).not.toContain('validated_production');
    expect(copy.ledger[1].body).toContain('0.035417 / 0.04375 / 0.031667');
    expect(copy.ledger[1].body).toContain('Q50 held at 0.020833');
    expect(copy.ledger[2].body).toContain('0.008929 / 0.018155 / 0.006845 / 0.001905');
    expect(copy.ledger[2].body).toContain('Not in production.');
    expect(copy.footnotes[1].tail).toContain('unmerged PR #23');
    expect(copy.footnotes[1].href).toContain(V15_PR23_SNAPSHOT.commit);
    expect(spanText(copy.caption)).toContain('fit only on timestamps before 2025-01-01');
    expect(spanText(copy.caption)).toContain('does not record its baseline training window');
    expect(spanText(copy.caption)).toContain('not directly comparable');
    expect(spanText(copy.caption)).not.toContain('0.874');
  });

  it('cites the version software DOI and the dataset DOI from the repo', () => {
    expect(citation.softwareDoi).toBe('10.5281/zenodo.23982227');
    expect(citation.conceptDoi).toBe('10.5281/zenodo.23982226');
    expect(citation.datasetDoi).toBe('10.5281/zenodo.22975251');
    expect(citation.version).toBe('1.2.0');
    expect(citation.author).toBe('Goehner, D.');
    expect(citation.year).toBe('2026');
  });
});

describe('homepage figure', () => {
  it('places the published points on the mockup scale', () => {
    const [q50, q90, q95, q99] = figure.columns;
    expect(q50.v14.square.y).toBeCloseTo(333.8356, 1);
    expect(q50.v15?.y).toBeCloseTo(421.2828, 1);
    expect(q50.v15?.y1).toBeCloseTo(165.12, 1);
    expect(q50.v15?.y2).toBeCloseTo(677.84, 1);
    expect(q90.v14.centerY).toBeCloseTo(722.8356, 1);
    expect(q50.v15?.note?.text).toBe('interval past the gate');
    expect(q90.v15?.note?.text).toBe('interval past the gate');
    expect(q95.v15?.note).toBeNull();
    expect(q99.v15?.note).toBeNull();
    expect(figure.columns.map((column) => column.v14.stub !== null)).toEqual([false, true, true, true]);
    expect(q99.v15?.labelY).toBeCloseTo(438, 0);
    expect(figure.legend.map((item) => item.label)).toEqual([
      'v1.4 point, n = 96',
      'v1.5, n = 672, Wilson 95%',
    ]);
  });
});

function studioPageRoutes(): string[] {
  const base = path.join(process.cwd(), 'app/(studio)');
  const routes: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name === 'page.tsx') {
        routes.push(`/${path.relative(base, path.dirname(full)).split(path.sep).join('/')}`);
      }
    }
  };
  walk(base);
  return routes.sort();
}

describe('homepage tool index', () => {
  it('links every studio route, so a new page with no homepage link fails', () => {
    expect(toolHrefs()).toEqual(studioPageRoutes());
  });

  it('describes the Historical Lab as a teaching exercise, not a forecast', () => {
    const history = toolEntries().find((entry) => entry.href === '/history');
    expect(history?.description).toContain(
      'deterministic teaching exercise over three deliberately chosen 72-hour windows',
    );
    expect(history?.description).toContain('not a validated forecast or a representative backtest');
  });
});

describe('homepage live fields', () => {
  it('stays unavailable for missing, estimated, and invented defaults', () => {
    expect(interpretLive(null, null).weather).toBe(UNAVAILABLE);
    expect(interpretLive(null, null).foot).toContain('UNAVAILABLE');
    const fallback = interpretLive(
      {
        temperature: 25,
        wind_speed: 10,
        solar_irradiance: 600,
        timestamp: '2026-11-10T15:00:00Z',
        data_source: 'estimated_fallback',
      },
      {
        current_load_mw: 45000,
        capacity_mw: 65000,
        timestamp: '2026-11-10T15:00:00Z',
        data_source: 'estimated_fallback',
        capacity_source: 'configured_reference',
        capacity_basis: 'configured ERCOT system reference',
      },
    );
    expect(fallback.weather).toBe(UNAVAILABLE);
    expect(fallback.load).toBe(UNAVAILABLE);
    expect(fallback.capacity).toBe(UNAVAILABLE);
    expect(fallback.asOfLabel).toBe(UNAVAILABLE);

    const monitorDefaults = interpretLive(
      { temperature: 32, wind_speed: 15, solar_irradiance: 800 },
      { current_load_mw: 45000, capacity_mw: 65000 },
    );
    expect(monitorDefaults.weather).toBe(UNAVAILABLE);
    expect(monitorDefaults.load).toBe(UNAVAILABLE);
    expect(JSON.stringify(monitorDefaults)).not.toContain('32');
    expect(JSON.stringify(monitorDefaults)).not.toContain('800');
  });

  it('shows an external forecast and official ERCOT values, and drops clear-sky solar', () => {
    const view = interpretLive(
      {
        temperature: 18.24,
        wind_speed: 3.41,
        solar_irradiance: 120.2,
        timestamp: '2026-11-10T15:41:00Z',
        data_source: 'external_forecast',
        provider: 'Open-Meteo',
        solar_source: 'external_forecast',
      },
      {
        current_load_mw: 61240.4,
        capacity_mw: 72100,
        timestamp: '2026-11-10T15:30:00Z',
        data_source: 'official_live',
        capacity_source: 'official_adequacy',
        capacity_basis: 'ERCOT available generation capacity (NP3-763-CD)',
      },
    );
    expect(view.weather).toBe('18.2°C · 3.4 m/s · 120 W/m²');
    expect(view.weatherDetail).toBe('Open-Meteo');
    expect(view.load).toBe('61,240 MW');
    expect(view.capacity).toBe('72,100 MW');
    expect(view.capacityDetail).toContain('NP3-763-CD');
    expect(view.asOfLabel).toBe('10 Nov 2026, 09:41');
    expect(view.foot).toBe('Weather forecast · load official · capacity official');

    const clearSky = interpretLive(
      {
        temperature: 4,
        wind_speed: 8,
        solar_irradiance: 640,
        timestamp: '2026-11-10T18:00:00Z',
        data_source: 'external_forecast',
        provider: 'NOAA/NWS',
        solar_source: 'clear_sky_estimate',
      },
      null,
    );
    expect(clearSky.weather).toBe('4.0°C · 8.0 m/s · solar UNAVAILABLE');
    expect(clearSky.load).toBe(UNAVAILABLE);
    expect(clearSky.capacity).toBe(UNAVAILABLE);
  });
});
