#!/bin/bash
set -u
cd /workspace/gert-v15
. /workspace/gert-venv/bin/activate
for i in 1 2 3 4 5; do
  python -m training.ercot.download_historical_load --start 2026-08-28 --end 2026-11-04 --output-dir training_data/ercot_np6_346_raw_segB && break
  echo "segB attempt $i failed; retrying in 60s"; sleep 60
done
for i in 1 2 3 4 5 6 7 8; do
  python -m training.ercot.download_historical_load --start 2019-01-01 --end 2025-01-02 --output-dir training_data/ercot_np6_346_raw_segA && break
  echo "segA attempt $i failed; retrying in 60s"; sleep 60
done
echo DOWNLOAD_DONE
