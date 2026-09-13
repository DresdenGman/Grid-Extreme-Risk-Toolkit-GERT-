"""Independently reproduce the Historical Lab calculation; optional browser report check.

python3 scripts/verify_historical_report.py --case summer-2023 --capacity 80000 --reduction 5
python3 scripts/verify_historical_report.py --report path/to/downloaded-report.json
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

DATASET_SHA256 = 'f403890ad50a654f85584e03642267d1a06bafb25bf4799346bbf87c4999181b'
ROOT = Path(__file__).resolve().parents[1]


def calculate(case, capacity, reduction):
    if not math.isfinite(capacity) or not 10000 <= capacity <= 120000:
        raise ValueError('Capacity must be 10000–120000 MW')
    if not math.isfinite(reduction) or not 0 <= reduction <= 20:
        raise ValueError('Reduction must be 0–20 percent')
    rows = []
    for hour in case['hours']:
        load = hour['load_mw']
        adjusted = load * (1 - reduction / 100)
        rows.append(dict(timestamp=hour['timestamp'], recordedLoadMw=load,
                         adjustedLoadMw=adjusted, assumedCapacityMw=capacity,
                         originalGapMw=max(0, load - capacity), adjustedGapMw=max(0, adjusted - capacity)))
    original = sum(row['originalGapMw'] for row in rows)
    adjusted = sum(row['adjustedGapMw'] for row in rows)
    peak = max(row['recordedLoadMw'] for row in rows)
    metrics = dict(recordedPeakMw=peak, adjustedPeakMw=max(row['adjustedLoadMw'] for row in rows),
                   originalHoursAboveCapacity=sum(row['originalGapMw'] > 0 for row in rows),
                   adjustedHoursAboveCapacity=sum(row['adjustedGapMw'] > 0 for row in rows),
                   originalGapMwh=original, adjustedGapMwh=adjusted, avoidedGapMwh=original-adjusted,
                   minimumUniformReductionPercent=max(0, 100 * (1 - capacity / peak)))
    return rows, metrics


def compare(expected, actual, location='report'):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            raise ValueError(f'{location}: fields differ')
        for key, value in expected.items():
            compare(value, actual[key], f'{location}.{key}')
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError(f'{location}: row count differs')
        for i, (left, right) in enumerate(zip(expected, actual)):
            compare(left, right, f'{location}[{i}]')
    elif isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(expected, actual, rel_tol=1e-10, abs_tol=1e-6):
            raise ValueError(f'{location}: numeric mismatch')
    elif actual != expected:
        raise ValueError(f'{location}: mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', default='summer-2023')
    parser.add_argument('--capacity', type=float, default=80000)
    parser.add_argument('--reduction', type=float, default=5)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    blob = (ROOT / 'public/data/historical-cases.json').read_bytes()
    if hashlib.sha256(blob).hexdigest() != DATASET_SHA256:
        raise ValueError('Dataset checksum mismatch: inspect the source before verifying')
    bundle = json.loads(blob)
    report = json.loads(args.report.read_text()) if args.report else None
    case_id = report['case_id'] if report else args.case
    case = next((case for case in bundle['cases'] if case['id'] == case_id), None)
    if case is None:
        raise ValueError('Unknown case')
    capacity = report['assumptions']['capacity_mw'] if report else args.capacity
    reduction = report['assumptions']['uniform_load_reduction_percent'] if report else args.reduction
    rows, metrics = calculate(case, capacity, reduction)
    if report:
        for key, value in {'schema': 'gert-historical-report-v1', 'analysis_version': 'historical-capacity-v1',
                           'dataset_version': bundle['version'], 'source_archive_sha256': case['source_archive_sha256'],
                           'source_url': case['source_url']}.items():
            compare(value, report.get(key), key)
        compare(1, report['assumptions']['interval_hours'], 'interval_hours')
        compare(rows, report['rows'], 'rows')
        compare(metrics, report['metrics'], 'metrics')
    print(json.dumps({'status': 'report_verified' if report else 'calculated', 'case': case_id,
                      'capacity_mw': capacity, 'reduction_percent': reduction, 'metrics': metrics}, indent=2))


if __name__ == '__main__':
    main()
