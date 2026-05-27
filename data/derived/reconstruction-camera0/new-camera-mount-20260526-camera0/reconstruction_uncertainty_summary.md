# Reconstruction uncertainty and systematic error summary

## Scope of this uncertainty model

- This is an offline, practical uncertainty treatment.
- It combines exact binomial confidence intervals where appropriate with interval-based temporal bounds and sensitivity analyses where exact propagation is not defensible.
- It does NOT claim lab-grade calibration of the webcam, LED output, or the OP598 timing chain.

## Key propagated outputs

- Pooled coincidence success rate on covered windows: `60/60 = 1.000` with Wilson 95% CI `[0.940, 1.000]`.
- Mean matched-frame offset: `49.7 +/- 20.1 ms from interval-based propagation of mean frame half-period and OP598 half sample-interval`.
- Minimum detectable duty statement: `practical conditional threshold is about duty 6-8, not a single exact duty, because the first success point has limited replicates and low-duty exposure response is non-monotonic`.
- Pulse-duration detectability statement: `practical webcam detectability starts around 50-100 ms depending on duty and exposure, with no evidence for a stable sub-50 ms threshold in the current dataset`.

## Systematic error terms included

- Webcam temporal quantization: mean half-frame uncertainty about `16.74 ms` from the selected runs' measured FPS.
- OP598 temporal anchoring under MicroPython cadence: mean half sample-interval about `3.34 ms` from `op598.sample_interval_avg_ms`.
- Threshold sensitivity: recomputed retained coincidence under stricter matched-frame thresholds of +10% and +20% using stored frame-threshold margins.
- Exposure dependence / low-duty non-monotonicity: low-duty exposure sweep spans `1.000` probability units, so the webcam threshold is conditional on exposure rather than monotonic.
- OP598 saturation: duties with saturation evidence in the characterization table: `[128, 512, 1023]`.
- Limited replicate counts: current derived tables mostly sit between `1` and `3` replicates per condition, often only one.

## Threshold sensitivity results

|   threshold_delta_fraction |   covered_pulses |   retained_matches |   retained_rate |
|---------------------------:|-----------------:|-------------------:|----------------:|
|                        0.1 |               60 |                 60 |               1 |
|                        0.2 |               60 |                 60 |               1 |

Interpretation: this is a one-sided robustness check against stricter thresholds. It does not re-run the full detector or estimate false-positive risk at lower thresholds, so it should be read as sensitivity, not absolute truth.

## Temporal uncertainty inputs by selected run

| run_id                       |   webcam_frame_period_ms |   webcam_half_period_ms |   op598_sample_interval_ms |   op598_half_sample_interval_ms |
|:-----------------------------|-------------------------:|------------------------:|---------------------------:|--------------------------------:|
| random-train_20260526_161408 |                  33.4743 |                 16.7372 |                    6.68897 |                         3.34449 |

## Honest limitations

- Stored offline artifacts do not preserve every pixel-level decision needed for a full end-to-end Monte Carlo of thresholding and matching.
- Exposure and duration sweeps are sparse, so uncertainty on detectability thresholds is better expressed as bounded practical ranges than precise estimates.
- OP598 saturation at high duty means amplitude-based interpretation there is not reliable, even if coincidence can still be observed.
- The propagated offset bound is conservative and interval-based; it is intentionally easier to defend than a pseudo-precise Gaussian claim.

Auxiliary sensitivity table written to `data/derived/reconstruction/threshold_sensitivity.csv`.
