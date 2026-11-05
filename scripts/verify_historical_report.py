"""Independently reproduce the Historical Lab calculation; optional browser report check.

python3 scripts/verify_historical_report.py --case summer-2023 --capacity 80000 --reduction 5
python3 scripts/verify_historical_report.py --report path/to/downloaded-report.json
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

DATASET_SHA256 = 'f403890ad50a654f85584e03642267d1a06bafb25bf4799346bbf87c4999181b'
ROOT = Path(__file__).resolve().parents[1]

REL_TOL = 1e-10
ABS_TOL = 1e-6
# Differences above the checker tolerance but within these bounds are
# consistent with values carried at lower precision than the source data
# (loads are recorded to 0.001 MW).
ROUNDING_ABS_LIMIT = 0.01
ROUNDING_REL_LIMIT = 1e-4
MAX_LISTED_MISMATCHES = 20


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
        if not isinstance(actual, (int, float)) or not math.isfinite(actual) or not math.isclose(expected, actual, rel_tol=REL_TOL, abs_tol=ABS_TOL):
            raise ValueError(f'{location}: numeric mismatch')
    elif actual != expected:
        raise ValueError(f'{location}: mismatch')


def compare_all(expected, actual, location='report', mismatches=None):
    """Collect every mismatch instead of stopping at the first one.

    Uses the same tolerance as compare(). Each entry records the path, the
    expected value, and the submitted value; numeric entries also record
    the difference (submitted - expected).
    """
    if mismatches is None:
        mismatches = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            mismatches.append({'path': location, 'expected': expected, 'actual': actual})
        elif set(expected) != set(actual):
            mismatches.append({'path': location,
                               'expected': 'fields ' + ', '.join(sorted(expected)),
                               'actual': 'fields ' + ', '.join(sorted(actual))})
        else:
            for key, value in expected.items():
                compare_all(value, actual[key], f'{location}.{key}', mismatches)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            mismatches.append({'path': location,
                               'expected': f'{len(expected)} rows',
                               'actual': f'{len(actual)} rows' if isinstance(actual, list) else actual})
        else:
            for i, (left, right) in enumerate(zip(expected, actual)):
                compare_all(left, right, f'{location}[{i}]', mismatches)
    elif isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)) or not math.isfinite(actual):
            mismatches.append({'path': location, 'expected': expected, 'actual': actual})
        elif not math.isclose(expected, actual, rel_tol=REL_TOL, abs_tol=ABS_TOL):
            mismatches.append({'path': location, 'expected': expected, 'actual': actual,
                               'difference': actual - expected})
    elif actual != expected:
        mismatches.append({'path': location, 'expected': expected, 'actual': actual})
    return mismatches


def format_value(value):
    if isinstance(value, float):
        return repr(value)
    return str(value) if isinstance(value, (int, str)) else repr(value)


def looks_like_rounding(mismatch):
    """True when a numeric difference is above tolerance but small enough
    to be explained by rounding or lower-precision intermediate values."""
    difference = mismatch.get('difference')
    if difference is None:
        return False
    return (abs(difference) <= ROUNDING_ABS_LIMIT
            or abs(difference) <= ROUNDING_REL_LIMIT * max(1.0, abs(mismatch['expected'])))


def rows_shift_amount(expected_rows, actual_rows):
    """Return +1 or -1 when the submitted rows match the expected rows
    displaced by one hour, else 0."""
    if not isinstance(actual_rows, list) or len(actual_rows) != len(expected_rows):
        return 0
    for shift in (1, -1):
        pairs = [(expected_rows[i], actual_rows[i + shift]) for i in range(len(expected_rows))
                 if 0 <= i + shift < len(actual_rows)]
        if pairs and all(not compare_all(left, right, 'row') for left, right in pairs):
            return shift
    return 0


def diagnose(report, expected_rows, mismatches):
    """Explain, in plain terms, why a report did not verify."""
    lines = [f'Report verification failed: {len(mismatches)} mismatch(es).', '']
    for mismatch in mismatches[:MAX_LISTED_MISMATCHES]:
        line = (f"  {mismatch['path']}: expected {format_value(mismatch['expected'])}, "
                f"report has {format_value(mismatch['actual'])}")
        if 'difference' in mismatch:
            line += f" (difference {format_value(mismatch['difference'])})"
        lines.append(line)
    if len(mismatches) > MAX_LISTED_MISMATCHES:
        lines.append(f'  ... and {len(mismatches) - MAX_LISTED_MISMATCHES} more')
    lines += ['', 'Likely causes:']
    notes = []
    assumptions = report.get('assumptions') if isinstance(report, dict) else None
    if isinstance(assumptions, dict):
        notes.append(f"- The check recomputes from the report's own assumptions: capacity "
                     f"{format_value(assumptions.get('capacity_mw'))} MW, uniform reduction "
                     f"{format_value(assumptions.get('uniform_load_reduction_percent'))}%. "
                     'If those are not the settings you intended, re-download the report '
                     'with the intended settings.')
    shift = rows_shift_amount(expected_rows, report.get('rows') if isinstance(report, dict) else None)
    if shift:
        direction = 'one hour later' if shift == 1 else 'one hour earlier'
        notes.append(f'- The hourly values match the expected rows shifted {direction}: the '
                     'rows are off by one hour. Timestamps are interval starts in '
                     'America/Chicago; check the timezone conversion.')
    rounded = [mismatch for mismatch in mismatches if looks_like_rounding(mismatch)]
    if rounded:
        notes.append(f'- {len(rounded)} difference(s) exceed the checker tolerance but are '
                     'small enough to be rounding: values carried at lower precision than '
                     'the source data (0.001 MW) do not verify exactly.')
    row_mismatch = next((mismatch for mismatch in mismatches
                         if mismatch['path'].startswith('rows[') and 'difference' in mismatch), None)
    if row_mismatch is not None:
        index = int(row_mismatch['path'].split('[')[1].split(']')[0])
        row = expected_rows[index]
        notes.append(f"- First mismatching row, rows[{index}] ({row['timestamp']}), with its "
                     'formula inputs so it can be checked by hand: '
                     f"recorded load {format_value(row['recordedLoadMw'])} MW; "
                     f"adjusted load = recorded x (1 - reduction / 100) = {format_value(row['adjustedLoadMw'])} MW; "
                     f"assumed capacity {format_value(row['assumedCapacityMw'])} MW; "
                     f"original gap = max(0, recorded - capacity) = {format_value(row['originalGapMw'])} MW; "
                     f"adjusted gap = max(0, adjusted - capacity) = {format_value(row['adjustedGapMw'])} MW. "
                     'A gap counts only when load is strictly above the assumed capacity; '
                     'an hour at or below capacity has a zero gap, however close it is to '
                     'the recorded peak.')
    if not notes:
        notes.append('- No pattern matched. Compare the first mismatching field by hand '
                     'against the formulas in docs/HISTORICAL_LAB.md.')
    lines.extend(notes)
    return '\n'.join(lines)


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
        mismatches = []
        for key, value in {'schema': 'gert-historical-report-v1', 'analysis_version': 'historical-capacity-v1',
                           'dataset_version': bundle['version'], 'source_archive_sha256': case['source_archive_sha256'],
                           'source_url': case['source_url']}.items():
            compare_all(value, report.get(key), key, mismatches)
        compare_all(1, report['assumptions']['interval_hours'], 'interval_hours', mismatches)
        compare_all(rows, report['rows'], 'rows', mismatches)
        compare_all(metrics, report['metrics'], 'metrics', mismatches)
        if mismatches:
            print(diagnose(report, rows, mismatches), file=sys.stderr)
            return 1
    print(json.dumps({'status': 'report_verified' if report else 'calculated', 'case': case_id,
                      'capacity_mw': capacity, 'reduction_percent': reduction, 'metrics': metrics}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
