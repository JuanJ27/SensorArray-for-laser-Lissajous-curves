# Tasks: Camera0 Intensity Threshold Statistics

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 520–780 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 tests+offline core → PR2 tooling/wrapper → PR3 ops task/docs |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | RED tests + offline plan/validation + analysis helpers | PR 1 | Main or feature branch; no hardware |
| 2 | Sweep wrapper/tooling adaptation for camera0 campaign execution | PR 2 | Depends on PR1; CLI + script wiring |
| 3 | Operational live-acquisition checklist task + preview gates | PR 3 | Depends on PR2; runbook-level safeguards |

## Phase 1: Offline Foundation (No Hardware)

- [x] 1.1 Add required constants/contracts (duty set, fixed 60 pulses per duty, controls, required columns) in `analysis/aggregate.py` and `analysis/uncertainty.py`.
- [x] 1.2 Add offline plan-generation mode in `tools/run_led_intensity_sweep.py` (`--emit-plan-only`) producing `data/derived/studies/camera0_intensity_campaign_plan.csv`.
- [x] 1.3 Add plan/metadata validation helpers in `analysis/aggregate.py` (campaign id, `camera_index=0`, acquisition fingerprint consistency, exclusion reasons).

## Phase 2: Strict TDD Test-First (RED→GREEN→REFACTOR)

- [x] 2.1 **RED**: Create `tests/test_camera0_plan_validation.py` for duty-plan completeness/incomplete, fixed 60 pulses, randomized/interleaved block checks.
- [x] 2.2 **RED**: Create `tests/test_camera0_filtering.py` for campaign/camera0 cohort inclusion, wrong-camera exclusion, missing-metadata exclusion reasons.
- [x] 2.3 **RED**: Create `tests/test_wilson_and_thresholds.py` for Wilson 95% bounds, duty50<=duty90<=duty95, bootstrap reproducibility.
- [x] 2.4 **GREEN**: Implement minimal code in `analysis/aggregate.py` + `analysis/uncertainty.py` to pass tests, using NumPy-first logistic/bootstrap fallback (SciPy/statsmodels only if already installed).
- [x] 2.5 **REFACTOR**: Reduce duplication and freeze deterministic seeds/fixtures without changing behavior.
- [x] 2.6 Add `tests/test_camera0_artifact_generation.py` to verify required outputs/columns and Spanish summary/plot labels.

## Phase 3: Tooling/Wiring for Camera0 Campaign

- [x] 3.1 Update `tools/run_led_intensity_sweep.py` CLI for required `--campaign-id`, `--run-intent threshold`, explicit `--index 0`, structured output metadata.
- [x] 3.2 Update `scripts/intensity_sweep.sh` as camera0 threshold wrapper with safe defaults and clear non-production warning paths.
- [x] 3.3 Ensure analysis writes `camera0_intensity_per_pulse.csv`, `camera0_intensity_by_duty_wilson.csv`, `camera0_threshold_estimates.csv`, `camera0_validation_report.csv`.

## Phase 4: Operational Acquisition Definition (Post-Tooling)

- [x] 4.1 Define live campaign execution task (no execution now) in `scripts/intensity_sweep.sh` usage/help: preview plan, preflight checks, explicit operator confirmation gates.
- [x] 4.2 Add acceptance checklist in `data/derived/presentation/camera0_intensity_threshold_summary.md` template including Spanish labels and required artifact presence.
