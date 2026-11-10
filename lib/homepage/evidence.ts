import { createHash } from 'crypto';
import { existsSync, readFileSync } from 'fs';
import path from 'path';
import { formatPlain, formatSignedAbsolute, formatUtcDate, formatWindow } from './format';
import {
  QUANTILE_ORDER,
  type CandidateSource,
  type CandidateView,
  type EvidenceModel,
  type QuantileId,
  type QuantilePoint,
} from './types';

/**
 * v1.5 evidence is not on main. Prefer evidence/ercot_v1_5_validation.json when
 * a build contains it. Otherwise read the verbatim PR #23 snapshot. The blob
 * hash is pinned so an in-place edit cannot move the figures.
 */
export const V15_PR23_SNAPSHOT = {
  localPath: 'evidence/snapshots/pr-23/ercot_v1_5_validation.json',
  upstreamPath: 'evidence/ercot_v1_5_validation.json',
  pr: 23,
  branch: 'feat/ercot-v1-5',
  commit: '98d4fbf82a78ebfaeca160bb0ac20915c8fc566e',
  blobSha1: '25f2dfadd717487be2db600c1478d1fa2f64cf86',
} as const;

const V14_PATH = 'evidence/ercot_v1_4_validation.json';

function repoRoot() {
  return process.cwd();
}

function gitBlobSha1(bytes: Buffer) {
  return createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function requiredString(record: Record<string, unknown>, key: string, file: string) {
  const value = record[key];
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`${file} is missing ${key}`);
  }
  return value;
}

function requiredNumber(record: Record<string, unknown>, key: string, file: string) {
  const value = record[key];
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`${file} field ${key} is not a finite number`);
  }
  return value;
}

function requiredBoolean(record: Record<string, unknown>, key: string, file: string) {
  const value = record[key];
  if (typeof value !== 'boolean') throw new Error(`${file} field ${key} is not boolean`);
  return value;
}

function versionFromId(candidateId: string) {
  const match = candidateId.match(/v(\d+\.\d+)/i);
  if (!match) throw new Error(`Cannot read a version from candidate id ${candidateId}`);
  return `v${match[1]}`;
}

function parseTolerance(requirement: string) {
  const match = requirement.match(/<=\s*([0-9]+(?:\.[0-9]+)?)/);
  if (!match) throw new Error(`Cannot read a calibration tolerance from "${requirement}"`);
  const value = Number(match[1]);
  if (!Number.isFinite(value) || value <= 0 || value >= 1) {
    throw new Error(`Calibration tolerance "${requirement}" is not usable`);
  }
  return value;
}

function quantileId(value: string, file: string): QuantileId {
  if ((QUANTILE_ORDER as readonly string[]).includes(value)) return value as QuantileId;
  throw new Error(`${file} has an unexpected quantile ${value}`);
}

function wilsonFrom(metric: Record<string, unknown>, file: string, quantile: string): [number, number] | null {
  if (!Object.prototype.hasOwnProperty.call(metric, 'coverage_wilson_95_ci')) return null;
  const value = metric.coverage_wilson_95_ci;
  if (!Array.isArray(value) || value.length !== 2) {
    throw new Error(`${file} ${quantile} Wilson interval is not a pair`);
  }
  const [low, high] = value;
  if (typeof low !== 'number' || typeof high !== 'number' || !Number.isFinite(low) || !Number.isFinite(high)) {
    throw new Error(`${file} ${quantile} Wilson interval is not numeric`);
  }
  if (low < 0 || high > 1 || low > high) {
    throw new Error(`${file} ${quantile} Wilson interval is out of range`);
  }
  return [low, high];
}

function parseCandidate(raw: unknown, file: string, source: CandidateSource) {
  if (!isRecord(raw)) throw new Error(`${file} is not a JSON object`);
  const candidateId = requiredString(raw, 'candidate_id', file);
  const status = requiredString(raw, 'validation_status', file);
  const summary = requiredString(raw, 'summary', file);
  const observations = requiredNumber(raw, 'observations', file);
  if (!Number.isInteger(observations) || observations <= 0) {
    throw new Error(`${file} observations must be a positive integer`);
  }
  const crossings = requiredNumber(raw, 'quantile_crossings', file);
  if (crossings < 0) throw new Error(`${file} quantile_crossings is negative`);
  const allGatesPassed = requiredBoolean(raw, 'all_gates_passed', file);
  const publishedAt = requiredString(raw, 'published_at', file);
  const windowStart = requiredString(raw, 'evaluation_window_start', file);
  const windowEnd = requiredString(raw, 'evaluation_window_end', file);
  const provenance = requiredString(raw, 'data_provenance', file);
  if (!Array.isArray(raw.limitations) || raw.limitations.some((item) => typeof item !== 'string')) {
    throw new Error(`${file} limitations must be a list of strings`);
  }
  const limitations = raw.limitations as string[];
  if (!Array.isArray(raw.gates) || !Array.isArray(raw.quantile_metrics)) {
    throw new Error(`${file} is missing gates or quantile metrics`);
  }
  const gates = raw.gates as unknown[];
  const quantileMetrics = raw.quantile_metrics as unknown[];

  const calibration = gates.filter((gate): gate is Record<string, unknown> => {
    return isRecord(gate) && typeof gate.gate === 'string' && /calibration error/i.test(gate.gate);
  });
  if (calibration.length === 0) throw new Error(`${file} has no calibration gates`);
  const tolerances = calibration.map((gate) => parseTolerance(requiredString(gate, 'requirement', file)));
  if (tolerances.some((value) => value !== tolerances[0])) {
    throw new Error(`${file} calibration gates do not share one tolerance`);
  }
  const tolerance = tolerances[0];

  const gateByQuantile = new Map<QuantileId, boolean>();
  for (const gate of calibration) {
    const name = requiredString(gate, 'gate', file);
    const match = name.match(/^(q\d+)/i);
    if (!match) throw new Error(`${file} calibration gate "${name}" has no quantile`);
    const id = quantileId(match[1].toLowerCase(), file);
    if (typeof gate.passed !== 'boolean') throw new Error(`${file} gate ${name} has no passed flag`);
    gateByQuantile.set(id, gate.passed);
  }

  if (!gates.every((gate) => isRecord(gate) && typeof gate.passed === 'boolean')) {
    throw new Error(`${file} has a gate without a passed flag`);
  }
  const everyPassed = gates.every((gate) => isRecord(gate) && gate.passed === true);
  if (everyPassed !== allGatesPassed) {
    throw new Error(`${file} all_gates_passed does not match the gate list`);
  }

  const points: QuantilePoint[] = QUANTILE_ORDER.map((quantile) => {
    const rows = quantileMetrics.filter((metric): metric is Record<string, unknown> => isRecord(metric) && metric.quantile === quantile);
    if (rows.length !== 1) throw new Error(`${file} must contain ${quantile} exactly once`);
    const metric = rows[0] as Record<string, unknown>;
    const nominal = requiredNumber(metric, 'target_coverage', file);
    const empirical = requiredNumber(metric, 'empirical_coverage', file);
    const absoluteError = requiredNumber(metric, 'absolute_coverage_error', file);
    if (nominal < 0 || nominal > 1 || empirical < 0 || empirical > 1 || absoluteError < 0) {
      throw new Error(`${file} ${quantile} coverage is out of range`);
    }
    formatSignedAbsolute(empirical, nominal, absoluteError);
    const pastGate = absoluteError > tolerance;
    const gatePassed = gateByQuantile.get(quantile);
    if (gatePassed === undefined) throw new Error(`${file} has no calibration gate for ${quantile}`);
    if (gatePassed === pastGate) {
      throw new Error(`${file} ${quantile} gate flag disagrees with absolute error ${absoluteError}`);
    }
    const wilson = wilsonFrom(metric, file, quantile);
    const signedWilson: [number, number] | null = wilson
      ? [wilson[0] - nominal, wilson[1] - nominal]
      : null;
    const intervalPastGate = signedWilson
      ? signedWilson[0] < -tolerance - 1e-6 || signedWilson[1] > tolerance + 1e-6
      : false;
    const delta = empirical - nominal;
    return {
      quantile,
      label: quantile.toUpperCase(),
      nominal,
      empirical,
      absoluteError,
      signedError: delta < 0 ? -absoluteError : absoluteError,
      pastGate,
      wilson,
      signedWilson,
      intervalPastGate,
    };
  });

  const text = `${provenance}\n${limitations.join('\n')}`;
  const candidate: CandidateView = {
    version: versionFromId(candidateId),
    candidateId,
    status,
    summary,
    observations,
    crossings,
    publishedLabel: formatUtcDate(publishedAt),
    windowLabel: formatWindow(windowStart, windowEnd),
    points,
    failedLabels: points.filter((point) => point.pastGate).map((point) => point.label),
    passedLabels: points.filter((point) => !point.pastGate).map((point) => point.label),
    allGatesPassed,
    mentionsEra5: /ERA5/i.test(text),
    realizedEra5: /realized ERA5/i.test(text),
    sameWeatherAsV14: /as in v1\.4/i.test(text),
    optimisticRealizedWeather: /may be optimistic|upper bound/i.test(text),
    gateUsesPointEstimate: /gate still uses the point estimate/i.test(text),
    wilsonComplete: points.every((point) => point.wilson !== null),
    source,
  };
  return { candidate, tolerance };
}

function readJson(relativePath: string) {
  return JSON.parse(readFileSync(path.join(repoRoot(), relativePath), 'utf8')) as unknown;
}

function loadV15() {
  const mainPath = 'evidence/ercot_v1_5_validation.json';
  if (existsSync(path.join(repoRoot(), mainPath))) {
    return parseCandidate(readJson(mainPath), mainPath, { kind: 'main', path: mainPath });
  }
  const absolute = path.join(repoRoot(), V15_PR23_SNAPSHOT.localPath);
  if (!existsSync(absolute)) return null;
  const bytes = readFileSync(absolute);
  const hash = gitBlobSha1(bytes);
  if (hash !== V15_PR23_SNAPSHOT.blobSha1) {
    throw new Error(
      `v1.5 snapshot hash ${hash} does not match the PR #23 blob ${V15_PR23_SNAPSHOT.blobSha1}`,
    );
  }
  return parseCandidate(JSON.parse(bytes.toString('utf8')) as unknown, V15_PR23_SNAPSHOT.localPath, {
    kind: 'pr23-snapshot',
    path: V15_PR23_SNAPSHOT.localPath,
    upstreamPath: V15_PR23_SNAPSHOT.upstreamPath,
    pr: V15_PR23_SNAPSHOT.pr,
    branch: V15_PR23_SNAPSHOT.branch,
    commit: V15_PR23_SNAPSHOT.commit,
  });
}

export function loadEvidence(): EvidenceModel {
  const v14 = parseCandidate(readJson(V14_PATH), V14_PATH, { kind: 'main', path: V14_PATH });
  const v15 = loadV15();
  if (v15 && v15.tolerance !== v14.tolerance) {
    throw new Error('v1.4 and v1.5 calibration tolerances differ; the figure will not draw a single gate');
  }
  const productionValidated = [v14.candidate, v15?.candidate].some(
    (candidate) => candidate?.status === 'validated_production',
  );
  return {
    tolerance: v14.tolerance,
    gateLabel: formatPlain(v14.tolerance),
    v14: v14.candidate,
    v15: v15?.candidate ?? null,
    productionValidated,
    windowsDiffer: v15 ? v14.candidate.windowLabel !== v15.candidate.windowLabel : false,
  };
}
