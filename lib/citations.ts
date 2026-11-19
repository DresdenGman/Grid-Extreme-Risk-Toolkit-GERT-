import releaseEvidence from '../evidence/ercot_v1_4_validation.json';

export const PRODUCT_NAME = 'Grid Extreme Risk Toolkit (GERT)';

export const SOFTWARE_CONCEPT_DOI = '10.5281/zenodo.23982226';
export const SOFTWARE_VERSION = '1.2.0';
export const SOFTWARE_PUBLISHED = '2026-11-05';

export const DATASET_DOI = '10.5281/zenodo.22975251';
export const DATASET_VERSION = 'v1';
export const DATASET_PUBLISHED = '2026-09-26';

/**
 * Headline J1/J2 figures from DresdenGman/PJM-Cold-Calibration-Benchmark
 * README, archived as Zenodo v1.0.0 (published 2026-11-06).
 * 12.5% is January 2014 polar-vortex hours, not every cold event.
 * 65.7% is the full 2014 evaluation period.
 */
export const PJM_BENCHMARK = {
  name: 'PJM-Cold-Calibration-Benchmark',
  repoUrl: 'https://github.com/DresdenGman/PJM-Cold-Calibration-Benchmark',
  doi: '10.5281/zenodo.24010850',
  version: '1.0.0',
  published: '2026-11-06',
  coldCoverage: '12.5%',
  fullPeriodCoverage: '65.7%',
  coldWindow: 'January 2014 polar-vortex hours',
  comparisonWindow: 'the full 2014 evaluation period',
  repair: '0 of 18 horizon × learner cells passed the pre-registered repair judgement',
} as const;

export const scenarioGateExplanation = `${releaseEvidence.candidate_id}: ${releaseEvidence.summary} Run Analysis stays disabled until a candidate passes every predeclared gate.`;

export function doiUrl(doi: string) {
  return `https://doi.org/${doi}`;
}

/** Counts from the 2026-11-17 re-run: pytest 142 passed, vitest 51 passed. */
export const TEST_RUN = {
  asOf: '2026-11-17',
  backend: 142,
  frontend: 51,
} as const;
