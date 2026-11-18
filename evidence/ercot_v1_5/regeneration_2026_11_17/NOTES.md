# ERCOT v1.5 frozen-config regeneration — 2026-11-17

These files were **regenerated on 2026-11-17 (America/Los_Angeles) from the frozen v1.5 configuration**.
They were **not archived at evaluation time** (2026-11-08). The published aggregates in
`evidence/ercot_v1_5/measurements.json` were not modified.

## Code and runtime
- Repository: DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-, branch `feat/ercot-v1-5`, HEAD `9dba63898bd29e98faacdc6c22df6560b9f9bf74`.
- `git diff 98d4fbf..9dba638 -- training models data` is empty (training code identical to the results commit).
- Python 3.12.16, numpy 1.26.4, scipy 1.14.1, pandas 2.3.3, scikit-learn 1.9.0, joblib 1.5.3, httpx 0.28.1 (pinned per requirements-training.txt / requirements.txt). random_state 42 (in code).
- Credentials came from process environment variables; no credential file was created, no value was printed or logged.

## Data
- Load: ERCOT NP6-346-CD archive (`/api/public-reports/archive/np6-346-cd`), downloaded with the repo's own `training.ercot.download_historical_load` (unmodified, 2.1 s request spacing).
  - Segment A: 2,194 daily ZIPs (post dates 2019-01-01..2025-01-02); extracted operating days 2019-01-01..2024-12-31 → 52,608 contiguous hourly rows.
  - Segment B: 69 daily ZIPs (post dates 2026-08-28..2026-11-04); extracted operating days 2026-08-28..2026-11-02 → 1,609 contiguous hourly rows.
  - One archive document per post day (checked against the archive listing for 2026-08-27..2026-11-05). Tabular API spot checks (2026-10-05, 2026-10-20, 2026-11-01) equal the archive values.
  - Two transient httpx ReadTimeouts during segment A; the downloader was re-run with file reuse (no file downloaded twice, every ZIP validated as one-CSV).
- Weather: Open-Meteo archive API, `models=era5`, the repo's four points and three variables.
  - 2019..2024 yearly files (`download_historical_weather --start-year 2019 --end-year 2024`).
  - 2026-08-28..2026-11-02 as one period file (`download_historical_weather_period`). The original run used several period files (last one 2026-10-31..2026-11-02); the join drops identical overlaps, so partitioning does not change values. Weather was pulled through 2026-11-02 only, to mirror the published run.
- Zone weights (from ≤2024 local-year load, as frozen): NORTH 0.3448663984, SOUTH 0.2612738293, WEST 0.1319804769, HOUSTON 0.2618792954.
- Joined rows: segment A 52,602 (2019-01-01T06Z..2024-12-31T23Z), segment B 1,603 (2026-08-28T05Z..2026-11-02T23Z). Both equal the published counts. Training rows 52,434 (equals the decision record).
- Missing / excluded hours (inner join, not imputed, outside every frozen window):
  - 2025-01-01 00:00–05:00Z (6 h, end of segment A; no 2025 weather in the frozen inputs).
  - 2026-11-03 00:00–05:00Z (6 h, end of segment B).
  - No gaps inside either segment; both per-segment audits passed (`data_quality_segA.json`, `data_quality_segB.json`).

## Commands (run from the repo root, in this order)
```
python -m training.ercot.download_historical_load --start 2026-08-28 --end 2026-11-04 --output-dir training_data/ercot_np6_346_raw_segB
python -m training.ercot.download_historical_load --start 2019-01-01 --end 2025-01-02 --output-dir training_data/ercot_np6_346_raw_segA   # re-run twice with reuse after ReadTimeouts
python -m training.ercot.download_historical_weather --start-year 2019 --end-year 2024 --output-dir training_data/ercot_weather_era5_segA
python -m training.ercot.download_historical_weather_period --start 2026-08-28 --end 2026-11-02 --output-dir training_data/ercot_weather_era5_2026
python -m training.ercot.extract_historical_load --raw-dir training_data/ercot_np6_346_raw_segA --supplemental-dir training_data/none --start 2019-01-01 --end 2024-12-31 --output training_data/ercot_load_segA.csv
python -m training.ercot.extract_historical_load --raw-dir training_data/ercot_np6_346_raw_segB --supplemental-dir training_data/none --start 2026-08-28 --end 2026-11-02 --output training_data/ercot_load_segB.csv
# concatenate segA+segB load -> training_data/ercot_load_combined.csv; copy both weather dirs into training_data/ercot_weather_era5_combined
python -m training.ercot.join_load_weather --load training_data/ercot_load_combined.csv --weather-dir training_data/ercot_weather_era5_combined --output training_data/ercot_hourly_joined.csv --manifest training_runs/ercot_v1/data_manifest.json
# split joined table at 2026 into segA/segB
python -m training.ercot.audit_training_data --load training_data/ercot_load_segA.csv --joined training_data/ercot_hourly_joined_segA.csv --output training_runs/ercot_v1/data_quality_segA.json
python -m training.ercot.audit_training_data --load training_data/ercot_load_segB.csv --joined training_data/ercot_hourly_joined_segB.csv --output training_runs/ercot_v1/data_quality_segB.json
python -m training.ercot.build_feature_table --input training_data/ercot_hourly_joined_segA.csv --output training_runs/ercot_v1/features_segA.csv
python -m training.ercot.build_feature_table --input training_data/ercot_hourly_joined_segB.csv --output training_runs/ercot_v1/features_segB.csv
# concatenate -> training_runs/ercot_v1/features.csv
python -m training.ercot.train_quantile_model --features training_runs/ercot_v1/features.csv --calibration-mode grid --training-end 2025-01-01 --calibration-start 2026-09-07 --calibration-end 2026-10-04 --evaluation-start 2026-10-05 --evaluation-end 2026-11-01 --model-version ercot-lag-residual-gbt-v1.5-candidate
python export_rows.py training_runs/ercot_v1/features.csv training_runs/ercot_v1/artifact <out>   # hourly rows from the saved model.joblib; refit check bit-identical
python compare.py <out>
```
Full scripts: `run_download.sh`, `run_pipeline.sh`, `export_rows.py`, `compare.py`, `diagnose_archive.py`.

## Tolerance
The repo defines no explicit regeneration tolerance. The checks that exist in
`scripts/recompute_ercot_v1_5_evidence.py` are: six-decimal uniqueness for coverages
(`inferred_covered_count`, |diff| ≤ 5.1e-7) and four-decimal equality for Wilson intervals.
`compare.py` applies |diff| ≤ 5.1e-7 to every published float, 4-dp equality to Wilson CIs,
and exact equality to counts and strings.

## Result
30 of 55 published values reproduce; 25 do not. **Every calibration-window value reproduces**
(base residual offsets, multipliers ×1.00, coverage before/after, window bounds, counts).
**Every evaluation-window score differs** (coverage, pinball, baseline pinball, skill, Wilson CI,
q50 MAE 311.05 vs 321.70 MW). Crossings (0) and finiteness still match.

What this rules in/out:
- Training data and the center model are the same as the original run: calibration offsets match to
  < 5e-7 MW, which needs the identical fitted center and identical calibration rows.
- The seasonal baseline depends only on training load and on the evaluation rows' actual load and
  month/hour. Its pinball also differs (q50 2323.22 vs 2312.44). So the evaluation-window
  actual load (2026-10-05..2026-11-01 UTC) that the original run used is not the same as what ERCOT
  NP6-346-CD returns today. The cause cannot be identified without the original rows, which were never archived.
- Regenerated rows are internally consistent: they reproduce the trainer's own report and the repo's
  `metrics_from_evaluation_rows` exactly.

## Gates
- Evidence-bundle gate: **NOT passed**. The published evaluation metrics do not reproduce.
- Feature-availability gate: **NOT passed** (realized ERA5 at evaluation; unchanged).
- The regenerated run's own numeric gates happen to pass (q90 |cov err| 0.0256 ≤ 0.03), and the trainer
  labels its own metadata `provisional_candidate`. This is not a promotion and does not replace the
  published result. It is a different measurement of the same frozen configuration.
