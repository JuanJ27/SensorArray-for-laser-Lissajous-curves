# Confidence and coverage notes for the reconstruction

## How each image was built

1. Select the best dual random-train runs with full webcam coverage and non-zero matched detections.
2. For each matched pulse, extract webcam frames at relative offsets `-2, -1, 0, +1, +2` around the matched frame.
3. Average pixel-wise within each relative phase to obtain `before`, `approach`, `hit`, `decay`, and `after` views.
4. Create contrast-normalized previews from those averages so the repeated flash pattern is visible without claiming radiometric calibration.
5. Report quantitative deltas against the pooled `before` phase in `reconstruction_statistics.csv`.

## Coverage and confidence annotations

- Selected runs: `1`.
- Matched pulses contributing to the pooled reconstruction: `60`.
- Effective sample size across runs (Kish-style by matched-pulse contribution): `1.00`.
- Pooled coincidence rate on covered windows: `1.000` with Wilson 95% CI `[0.940, 1.000]`.
- Pooled mean matched-frame offset: `49.66 ms`.

## Run-level variability at the hit phase

| run_id                       |   matched_pulses |   coverage_fraction |   coincidence_success_rate_windowed |   coincidence_success_ci_low |   coincidence_success_ci_high |   mean_offset_ms_detected |   offset_std_ms_detected |
|:-----------------------------|-----------------:|--------------------:|------------------------------------:|-----------------------------:|------------------------------:|--------------------------:|-------------------------:|
| random-train_20260526_161408 |               60 |                   1 |                                   1 |                     0.939826 |                             1 |                   49.6556 |                  9.97509 |

## Interpretation discipline

- Higher `frame_count` means more repeated evidence contributed to that phase average.
- `effective_sample_size` tells you whether the pooled image comes from several runs or is dominated by one run.
- `delta_mean_gray_vs_before` is a simple summary of how much brighter a phase is than the pooled pre-flash phase; it is useful for interpretability, not for absolute photometry.
- The comparison panel should be read together with the confidence intervals and offset spread, not as standalone proof of high-speed temporal imaging.
