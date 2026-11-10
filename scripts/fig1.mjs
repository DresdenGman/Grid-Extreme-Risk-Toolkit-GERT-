import { readFileSync } from 'node:fs';

function load(file) {
  return JSON.parse(readFileSync(file, 'utf8'));
}

function series(doc) {
  return doc.quantile_metrics.map((metric) => ({
    quantile: metric.quantile,
    nominal: metric.target_coverage,
    empirical: metric.empirical_coverage,
    absolute_coverage_error: metric.absolute_coverage_error,
    signed_coverage_error: metric.empirical_coverage - metric.target_coverage,
    wilson_95: metric.coverage_wilson_95_ci ?? null,
    observations: doc.observations,
    validation_status: doc.validation_status,
  }));
}

const v14 = load('evidence/ercot_v1_4_validation.json');
const v15Path = 'evidence/ercot_v1_5_validation.json';
let v15File = 'evidence/snapshots/pr-23/ercot_v1_5_validation.json';
try {
  load(v15Path);
  v15File = v15Path;
} catch {
  // The unmerged candidate is not on main. The snapshot is the copy Fig. 1 uses.
}
const v15 = load(v15File);

process.stdout.write(`${JSON.stringify({
  v14_file: 'evidence/ercot_v1_4_validation.json',
  v15_file: v15File,
  v14: series(v14),
  v15: series(v15),
}, null, 2)}\n`);
