# Historical Lab: sources and reproduction

Try the [Historical Lab](https://gert-d.vercel.app/history) and the
[independent review guide](https://gert-d.vercel.app/review).

This release contains 216 hourly observations in three deliberately selected
72-hour examples: August 9–11, 2023; April 10–12, 2023; February 14–16, 2021.
They illustrate different load profiles and are not a representative validation
sample or a forecast backtest.

## Sources

The observations come directly from [ERCOT's public native-load archives](https://www.ercot.com/gridinfo/load/load_hist).
Each dataset case links the original ZIP and records its SHA-256. The extractor
uses column `ERCOT` in the official workbook and rounds to 0.001 MW. The bundled
dataset has a separate SHA-256 in `public/data/historical-cases.sha256`.

Native load is not the same series as the forecast-zone data used by the
probabilistic research candidate. No candidate model or private research data
is used by this lab. ERCOT is the data source, not an endorser of GERT.

Time labels are hourly interval starts in America/Chicago, converted from
ERCOT's market-local Hour Ending field (hour 24 ends at the next midnight).
Each selected window avoids daylight-saving transitions and contains exactly
72 unique, contiguous one-hour intervals.

For winter 2021, recorded load was affected by outages and load shedding. It
cannot recover the demand that would have existed without those events.

## Rebuild the dataset

Use Python 3.10+ and curl. No Python packages or credentials are required.

```bash
mkdir -p /tmp/gert-archive-check
curl --fail --location https://www.ercot.com/files/docs/2023/02/09/Native_Load_2023.zip --output /tmp/gert-archive-check/gert-native-load-2023.zip
curl --fail --location https://www.ercot.com/files/docs/2021/11/12/Native_Load_2021.zip --output /tmp/gert-archive-check/gert-native-load-2021.zip
python3 scripts/build_historical_cases.py --archive-dir /tmp/gert-archive-check
git diff --exit-code -- public/data
```

The last command checks that rebuilding the public source produces the same
files. If ERCOT revises an archive, inspect the difference and version the
dataset; do not silently replace the recorded checksum.

## Independent numerical check

```bash
python3 scripts/verify_historical_report.py --case summer-2023 --capacity 80000 --reduction 5
python3 scripts/verify_historical_report.py --report /path/to/gert-summer-2023-report.json
```

The second command verifies a JSON report downloaded in the browser against the
bundled source, every hourly calculation, and every summary metric. It fails on
a checksum mismatch, changed observation, invalid assumption, or wrong result.
Its Python calculations are independent of the browser's TypeScript code.

## Mathematics and interpretation

For recorded load L(t), constant assumed capacity C, and uniform reduction r:

```text
Adjusted load(t) = L(t) × (1 − r / 100)
Gap power(t) = max(0, adjusted load(t) − C)                 [MW]
Gap energy = sum over all hours of Gap power(t) × 1 hour  [MWh]
Minimum uniform reduction = max(0, 100 × (1 − C / max L)) [%]
```

The positive-part function makes gap energy piecewise linear in capacity and
reduction. Summing hourly power gaps is a discrete integral. Exceedance hours
count intervals with a strictly positive gap; equality has zero gap. The
minimum reduction clears the peak algebraically under these assumptions.

Capacity is a user assumption, not historical capacity. The reduction is a
counterfactual, not a measured intervention. The exercise does not establish
feasibility, outage avoidance, financial savings, or expected unserved energy.
It omits generation constraints, transmission, reserves, uncertainty, and cost.
Research-candidate calibration and production-inference gates are unchanged.

## Contribute a review

Use the repository's **Historical Lab independent review** issue template.
Report your inputs, the result you checked, and one specific criticism. A
verified reproduction, an interface review, a workshop, and operational adoption
are recorded separately. A GitHub star or a page view is not a completed test.
