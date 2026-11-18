#!/bin/bash
set -euxo pipefail
cd /workspace/gert-v15
. /workspace/gert-venv/bin/activate
st(){ echo "- $(date +%T) PST: $*" >> /workspace/gert-v15-regen/STATUS.md; }
st "pipeline started at git $(git rev-parse HEAD)"
TD=training_data
python -m training.ercot.extract_historical_load --raw-dir $TD/ercot_np6_346_raw_segA --supplemental-dir $TD/none --start 2019-01-01 --end 2024-12-31 --output $TD/ercot_load_segA.csv
st "done: python -m training.ercot.extract_historical_load"
python -m training.ercot.extract_historical_load --raw-dir $TD/ercot_np6_346_raw_segB --supplemental-dir $TD/none --start 2026-08-28 --end 2026-11-02 --output $TD/ercot_load_segB.csv
st "done: python -m training.ercot.extract_historical_load"
{ cat $TD/ercot_load_segA.csv; tail -n +2 $TD/ercot_load_segB.csv; } > $TD/ercot_load_combined.csv
st "done: { cat $TD/ercot_load_segA.csv; tail -n +2 $TD/ercot_load_segB.csv; } > $TD/ercot_load_comb"
rm -rf $TD/ercot_weather_era5_combined && mkdir $TD/ercot_weather_era5_combined
cp $TD/ercot_weather_era5_segA/*.json $TD/ercot_weather_era5_2026/*.json $TD/ercot_weather_era5_combined/
st "done: cp $TD/ercot_weather_era5_segA/*.json $TD/ercot_weather_era5_2026/*.json $TD/ercot_weather"
python -m training.ercot.join_load_weather --load $TD/ercot_load_combined.csv --weather-dir $TD/ercot_weather_era5_combined --output $TD/ercot_hourly_joined.csv --manifest training_runs/ercot_v1/data_manifest.json
st "done: python -m training.ercot.join_load_weather"
python - <<'PY'
import pandas as pd
j = pd.read_csv("training_data/ercot_hourly_joined.csv")
a = j[j.timestamp_utc < "2026"]; b = j[j.timestamp_utc >= "2026"]
a.to_csv("training_data/ercot_hourly_joined_segA.csv", index=False); b.to_csv("training_data/ercot_hourly_joined_segB.csv", index=False)
print("segA joined", len(a), a.timestamp_utc.iloc[0], a.timestamp_utc.iloc[-1]); print("segB joined", len(b), b.timestamp_utc.iloc[0], b.timestamp_utc.iloc[-1])
PY
st "done: split joined table per segment"
python -m training.ercot.audit_training_data --load $TD/ercot_load_segA.csv --joined $TD/ercot_hourly_joined_segA.csv --output training_runs/ercot_v1/data_quality_segA.json > /dev/null
st "done: python -m training.ercot.audit_training_data"
python -m training.ercot.audit_training_data --load $TD/ercot_load_segB.csv --joined $TD/ercot_hourly_joined_segB.csv --output training_runs/ercot_v1/data_quality_segB.json > /dev/null
st "done: python -m training.ercot.audit_training_data"
python -m training.ercot.build_feature_table --input $TD/ercot_hourly_joined_segA.csv --output training_runs/ercot_v1/features_segA.csv
st "done: python -m training.ercot.build_feature_table"
python -m training.ercot.build_feature_table --input $TD/ercot_hourly_joined_segB.csv --output training_runs/ercot_v1/features_segB.csv
st "done: python -m training.ercot.build_feature_table"
{ cat training_runs/ercot_v1/features_segA.csv; tail -n +2 training_runs/ercot_v1/features_segB.csv; } > training_runs/ercot_v1/features.csv
st "done: { cat training_runs/ercot_v1/features_segA.csv; tail -n +2 training_runs/ercot_v1/features"
python -m training.ercot.train_quantile_model --features training_runs/ercot_v1/features.csv --calibration-mode grid --training-end 2025-01-01 --calibration-start 2026-09-07 --calibration-end 2026-10-04 --evaluation-start 2026-10-05 --evaluation-end 2026-11-01 --model-version ercot-lag-residual-gbt-v1.5-candidate > training_runs/ercot_v1/train_stdout.json
st "done: python -m training.ercot.train_quantile_model"
OUT=/workspace/gert-v15-regen
rm -rf $OUT/artifact && cp -r training_runs/ercot_v1/artifact $OUT/artifact
st "done: rm -rf $OUT/artifact && cp -r training_runs/ercot_v1/artifact $OUT/artifact"
cp training_runs/ercot_v1/data_manifest.json training_runs/ercot_v1/data_quality_seg*.json $OUT/
st "done: cp training_runs/ercot_v1/data_manifest.json training_runs/ercot_v1/data_quality_seg*.json"
python $OUT/export_rows.py training_runs/ercot_v1/features.csv training_runs/ercot_v1/artifact $OUT
st "done: python $OUT/export_rows.py training_runs/ercot_v1/features.csv training_runs/ercot_v1/arti"
python $OUT/compare.py $OUT
st "done: python $OUT/compare.py $OUT"
st "PIPELINE_DONE"
echo PIPELINE_DONE
