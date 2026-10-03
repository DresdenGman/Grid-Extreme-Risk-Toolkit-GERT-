"""Describe finite-sample tail coverage; never change a production gate.

python scripts/diagnose_tail_sample.py
Only the Python standard library is required. IID calculations are illustrative:
hourly grid forecast errors may be dependent.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def diagnose(evidence, tolerance=0.03):
    n = evidence['observations']
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 1000000:
        raise ValueError('observations must be an integer between 1 and 1000000')
    if not math.isfinite(tolerance) or not 0 <= tolerance <= 1:
        raise ValueError('tolerance must be finite and between 0 and 1')
    rows = []
    for row in evidence['quantile_metrics']:
        q, coverage = row['target_coverage'], row['empirical_coverage']
        if not math.isfinite(q) or not 0 < q < 1:
            raise ValueError('target coverage must be finite and strictly between 0 and 1')
        if not math.isfinite(coverage) or not 0 <= coverage <= 1:
            raise ValueError('empirical coverage must be finite and between 0 and 1')
        covered = round(n * coverage)
        # The public evidence rounds coverage to six decimal places.
        if abs(covered/n - coverage) > 0.00000051:
            raise ValueError('coverage is inconsistent with an integer count at six-decimal precision')
        low = max(0, math.ceil(n*(q-tolerance)-1e-9))
        high = min(n, math.floor(n*(q+tolerance)+1e-9))
        rows.append({
            'quantile': row['quantile'],
            'covered_count_inferred_from_rounded_summary': covered,
            'exceedance_count_inferred_from_rounded_summary': n-covered,
            'exceedance_count_range_accepted_by_tolerance': [n-high, n-low] if low <= high else None,
            'iid_expected_exceedances_at_target': n*(1-q),
            'iid_probability_zero_exceedances_at_target': q**n,
            'iid_zero_failure_min_n_for_one_sided_95pct_upper_rate_at_most_nominal':
                math.ceil(math.log(.05)/math.log(q)),
        })
    return {
        'schema': 'gert-tail-sample-diagnostic-v1',
        'candidate_id': evidence['candidate_id'],
        'source_validation_status': evidence['validation_status'],
        'observations': n,
        'coverage_step_percentage_points': 100/n,
        'illustrative_absolute_coverage_tolerance': tolerance,
        'quantiles': rows,
        'authority': 'sample-size diagnostic only; not a calibration test or promotion decision',
        'limitations': [
            'Counts are inferred from rounded aggregate evidence, not raw forecast residuals.',
            'Binomial calculations assume independent Bernoulli trials; hourly errors may be dependent.',
            'Hours are not independent extreme events; no event-level performance is established.',
            'Zero exceedances do not prove calibration; wide conservative intervals can also produce zero exceedances.',
            'No candidate, threshold, serving artifact or production authorization is changed.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT/'evidence/ercot_v1_4_validation.json')
    parser.add_argument('--tolerance', type=float, default=0.03,
                        help='Illustrative diagnostic tolerance; does not change the candidate contract')
    args = parser.parse_args()
    raw = args.evidence.read_bytes()
    try:
        result = diagnose(json.loads(raw), args.tolerance)
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    result['source_evidence_sha256'] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
