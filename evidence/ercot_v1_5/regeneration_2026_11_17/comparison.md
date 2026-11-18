# v1.5 published vs regenerated (2026-11-17)

Tolerance: floats |diff| <= 5.1e-07 (repo six-decimal check); Wilson CI equal at 4 dp; counts/strings exact.

Result: 30/55 match. All reproduced: no.

| metric | published | regenerated | abs diff | match |
|---|---|---|---|---|
| observations | 672 | 672 | 0 | yes |
| calibration_observations | 672 | 672 | 0 | yes |
| calibration_window_start | 2026-09-07T00:00:00Z | 2026-09-07T00:00:00Z |  | yes |
| calibration_window_end | 2026-10-04T23:00:00Z | 2026-10-04T23:00:00Z |  | yes |
| evaluation_window_start | 2026-10-05T00:00:00Z | 2026-10-05T00:00:00Z |  | yes |
| evaluation_window_end | 2026-11-01T23:00:00Z | 2026-11-01T23:00:00Z |  | yes |
| q50_mae_mw | 321.7034248 | 311.051774 | 10.65165081 | NO |
| quantile_crossings | 0 | 0 | 0 | yes |
| quantile_crossing_rate | 0 | 0 | 0 | yes |
| finite_predictions_observed | all 672 evaluation rows finite | all 672 evaluation rows finite |  | yes |
| calibration.mode | grid | grid |  | yes |
| calibration.base_residual_offsets_mw.q50 | 138.704963 | 138.7049627 | 3.457315358e-07 | yes |
| calibration.multipliers.q50 | 1 | 1 | 0 | yes |
| calibration.calibration_coverage_after.q50 | 0.5 | 0.5 | 0 | yes |
| calibration.calibration_coverage_before.q50 | 0.403274 | 0.4032738095 | 1.904761905e-07 | yes |
| calibration.base_residual_offsets_mw.q90 | 705.51378 | 705.5137804 | 4.191180096e-07 | yes |
| calibration.multipliers.q90 | 1 | 1 | 0 | yes |
| calibration.calibration_coverage_after.q90 | 0.89881 | 0.8988095238 | 4.761904762e-07 | yes |
| calibration.calibration_coverage_before.q90 | 0.889881 | 0.8898809524 | 4.761904771e-08 | yes |
| calibration.base_residual_offsets_mw.q95 | 886.919353 | 886.9193529 | 1.323837751e-07 | yes |
| calibration.multipliers.q95 | 1 | 1 | 0 | yes |
| calibration.calibration_coverage_after.q95 | 0.949405 | 0.9494047619 | 2.380952382e-07 | yes |
| calibration.calibration_coverage_before.q95 | 0.931548 | 0.931547619 | 3.80952381e-07 | yes |
| calibration.base_residual_offsets_mw.q99 | 1182.658076 | 1182.658076 | 2.90469643e-07 | yes |
| calibration.multipliers.q99 | 1 | 1 | 0 | yes |
| calibration.calibration_coverage_after.q99 | 0.989583 | 0.9895833333 | 3.333333334e-07 | yes |
| calibration.calibration_coverage_before.q99 | 0.889881 | 0.8898809524 | 4.761904771e-08 | yes |
| q50.empirical_coverage | 0.508929 | 0.5148809524 | 0.005951952381 | NO |
| q50.absolute_coverage_error | 0.008929 | 0.01488095238 | 0.005951952381 | NO |
| q50.pinball_loss | 160.851712 | 155.525887 | 5.325824996 | NO |
| q50.baseline_pinball_loss | 2312.438609 | 2323.220041 | 10.78143204 | NO |
| q50.pinball_skill_vs_baseline | 0.930441 | 0.9330558947 | 0.002614894725 | NO |
| q50.coverage_wilson_95_ci | [0.471200, 0.546600] | [0.477117, 0.552476] | 0.005916937625 | NO |
| q50.target_coverage | 0.5 | 0.5 | 0 | yes |
| q90.empirical_coverage | 0.918155 | 0.9255952381 | 0.007440238095 | NO |
| q90.absolute_coverage_error | 0.018155 | 0.0255952381 | 0.007440238095 | NO |
| q90.pinball_loss | 76.691465 | 74.84429493 | 1.847170074 | NO |
| q90.baseline_pinball_loss | 1120.3762 | 1120.299489 | 0.07671085345 | NO |
| q90.pinball_skill_vs_baseline | 0.931548 | 0.933192601 | 0.00164460104 | NO |
| q90.coverage_wilson_95_ci | [0.895000, 0.936600] | [0.903244, 0.943109] | 0.008243806891 | NO |
| q90.target_coverage | 0.9 | 0.9 | 0 | yes |
| q95.empirical_coverage | 0.956845 | 0.962797619 | 0.005952619048 | NO |
| q95.absolute_coverage_error | 0.006845 | 0.01279761905 | 0.005952619048 | NO |
| q95.pinball_loss | 45.982329 | 45.1289826 | 0.8533463981 | NO |
| q95.baseline_pinball_loss | 686.257936 | 686.2195808 | 0.03835516472 | NO |
| q95.pinball_skill_vs_baseline | 0.932996 | 0.9342353616 | 0.001239361592 | NO |
| q95.coverage_wilson_95_ci | [0.938700, 0.969800] | [0.945658, 0.974676] | 0.006958132153 | NO |
| q95.target_coverage | 0.95 | 0.95 | 0 | yes |
| q99.empirical_coverage | 0.988095 | 0.9895833333 | 0.001488333333 | NO |
| q99.absolute_coverage_error | 0.001905 | 0.0004166666667 | 0.001488333333 | NO |
| q99.pinball_loss | 11.09114 | 11.05097592 | 0.04016407589 | NO |
| q99.baseline_pinball_loss | 198.961765 | 198.9540937 | 0.007671327446 | NO |
| q99.pinball_skill_vs_baseline | 0.944255 | 0.9444546442 | 0.0001996441839 | NO |
| q99.coverage_wilson_95_ci | [0.976700, 0.994000] | [0.978656, 0.994945] | 0.001955926124 | NO |
| q99.target_coverage | 0.99 | 0.99 | 0 | yes |
