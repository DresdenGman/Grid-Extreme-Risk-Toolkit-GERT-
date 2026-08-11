# ERCOT model-training boundary

This directory describes a GERT-only, offline pipeline. It does not read or
write any research-project directory and it is not imported by the production
API.

## Served-model contract

Artifact schema 1.2 accepts target-hour `temperature` (°C), `wind_speed`
(m/s), `solar_irradiance` (W/m²), plus ERCOT-local `hour`, `day_of_week`,
`month`, `is_weekend`, and `year`. The raw joined table contains:

```text
timestamp_utc, actual_load_mw, temperature_c, wind_speed_ms, solar_irradiance_wm2
```

`training.ercot.features.build_serving_feature_rows` derives the calendar
features with the `America/Chicago` timezone. Inputs must be UTC-normalized
and contiguous hourly observations; gaps are rejected rather than imputed.

The model target is ERCOT system-wide load one hour ahead. Production weather
uses a fixed-weight aggregation of Dallas/North, San Antonio/South,
Midland/West, and Houston forecasts. The weights are derived only from the
2019–2024 training period; 2025 is held out.

## Reproducible pipeline

```bash
python -m training.ercot.download_historical_load
python -m training.ercot.recover_historical_load_day --day 2025-12-04
python -m training.ercot.download_historical_weather
python -m training.ercot.download_weather_boundary
python -m training.ercot.extract_historical_load
python -m training.ercot.join_load_weather
python -m training.ercot.audit_training_data
python -m training.ercot.build_feature_table \
  --input training_data/ercot_hourly_joined.csv \
  --output training_runs/ercot_v1/features.csv
python -m training.ercot.train_quantile_model
```

Sources:

- ERCOT NP6-346-CD official historical archives and tabular API recovery.
- Open-Meteo Historical Weather API using the consistent hourly ERA5 model:
  https://open-meteo.com/en/docs/historical-weather-api

## Important limitation

The PJM paper's lagged-load and rolling-window features are **not** included.
They require an operational feature store that can reproduce those features at
prediction time. Historical training uses realized ERA5 target-hour weather,
while production uses a one-hour weather forecast; evaluation therefore does
not measure weather-forecast error and may be optimistic.

WIS is not reported for the runtime bundle because it exposes upper quantiles
only (`q50`, `q90`, `q95`, `q99`). Pinball loss and empirical coverage are
reported for every served quantile.

The candidate uses a log-linear annual-mean trend because tree models cannot
extrapolate demand growth beyond their training years. A median normalized-load
model is combined with ordered residual quantiles calibrated on three strictly
out-of-sample rolling years (2022, 2023, and 2024). This prevents quantile
crossing by construction. The annual trend can still miss future structural
breaks.

## Latest locked holdout result

The 2025 holdout contains 8,760 hours and is not used for fitting or
calibration. The current `v1.2.0-candidate` improved pinball loss versus the
trend-adjusted month/hour climatology at every served quantile and achieved a
q50 MAE of 1,644.26 MW. Its q50/q90/q95/q99 empirical coverages were
0.5009/0.9376/0.9752/0.9974. The candidate did **not** pass the predeclared
promotion gate because q90's absolute coverage error was 0.0376, above 0.03.
It must remain outside `models/production/`; the threshold must not be relaxed
after observing the holdout.

After freezing that design, the pipeline was extended without overwriting v1:
the model was retrained on 2019–2025 and evaluated on a newly acquired,
previously unseen 2026-01-01 through 2026-06-30 holdout (4,343 DST-correct
hours). Data quality passed, and pinball skill versus the same fair baseline
was positive at every quantile (57.0%–65.0%). However, empirical coverage was
0.7283/0.9751/0.9878/0.9986, so the fresh candidate also failed the 0.03
coverage-error gate. This independently confirms that the current static
weather/calendar architecture is not sufficiently calibrated for promotion.
The next model class should add operationally reproducible lagged-load and
rolling-demand features, then use a new untouched evaluation window.

## Data isolation

Place local source extracts under `training_data/` and experiment outputs under
`training_runs/`. Both paths are ignored by Git. Never place a model in
`models/production/` until its ERCOT domain, training period, runtime versions,
and evaluation metrics pass the real-model artifact gate.

## Isolated dependencies

Use `requirements-training.txt` only in a dedicated local training environment.
The smaller pinned NumPy/SciPy/scikit-learn subset in `requirements.txt` is
required to load a gated artifact in Railway's inference runtime; pandas stays
training-only.
