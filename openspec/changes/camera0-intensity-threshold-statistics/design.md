# Design: Camera0 Intensity Threshold Statistics

## Technical Approach

Implement a **camera0 campaign lane** on top of the existing intensity sweep + offline aggregation flow, without triggering hardware in this phase. The implementation path is: (1) generate a deterministic randomized plan for required duties and controls, (2) execute later with camera0-only metadata (`campaign_id`, `index=0`, `run_intent`), (3) build a per-pulse dataset, then (4) compute duty-level Wilson CIs and duty50/duty90/duty95 from logistic + bootstrap summaries. Legacy `index=2` rows remain readable but are excluded by contract.

## Architecture Decisions

| Decision | Options | Tradeoff | Decision |
|---|---|---|---|
| Campaign identity | Infer from filenames vs explicit metadata columns | Inference is brittle and unsafe for exclusion rules | Add mandatory `campaign_id`, `camera_index`, `run_intent` fields and fail validation when missing |
| Replication model | Keep `count=3` train-per-duty vs pulse-level interleaved blocks | Current model is underpowered and order-biased | Use randomized block plan with `count=1` per step; total pulses per duty >=30 (target 50–100) |
| Stats implementation | Only descriptive rates vs inferential model + resampling | Descriptive-only cannot estimate threshold uncertainty | Add Wilson CI per duty plus logistic fit and bootstrap CIs for duty50/90/95 |
| Output integration | New one-off notebook vs repository CSV+MD+plots pipeline | Notebook-only is less reproducible in CI/ops | Extend scriptable outputs under `data/derived/studies` + `data/derived/presentation` |

## Data Flow

```text
Plan generator (no acquisition)
  -> data/derived/studies/camera0_intensity_campaign_plan.csv
  -> validates duties, controls, replication targets

Future run execution (apply phase)
  -> tools/run_led_intensity_sweep.py --index 0 --campaign-id ... --run-intent threshold
  -> raw run CSVs in data/webcam/

Analysis step
  -> per-pulse table (camera0 + campaign filtered)
  -> per-duty Wilson CI table
  -> logistic + bootstrap threshold table
  -> plots with error bars
```

## File Changes

| File | Action | Description |
|---|---|---|
| `tools/run_led_intensity_sweep.py` | Modify | Add campaign metadata flags (`--campaign-id`, `--run-intent`, `--index` default stays explicit at call site), optional plan-generation mode (`--emit-plan-only`), and structured output columns for camera0 cohort filtering. Remove legacy pooling behavior by requiring explicit campaign filter in analysis input path. |
| `scripts/intensity_sweep.sh` | Modify | Convert to camera0 campaign wrapper defaults (`--index 0`, required campaign id, required fixed acquisition params), plus non-production warning split: tuning vs threshold campaign script mode. |
| `analysis/aggregate.py` | Modify | Add `collect_camera0_intensity_threshold(...)` to build per-pulse rows, per-duty Wilson CI rows, and campaign-scoped summaries; enforce exclusion reasons for wrong camera/metadata/campaign. |
| `analysis/uncertainty.py` | Modify | Add reusable helpers for logistic threshold estimation and bootstrap percentile intervals (duty50/duty90/duty95). |
| `data/derived/studies/*` | Create (generated later) | New outputs: `camera0_intensity_per_pulse.csv`, `camera0_intensity_by_duty_wilson.csv`, `camera0_threshold_estimates.csv`, `camera0_validation_report.csv`. |
| `data/derived/presentation/*` | Create (generated later) | New plots/summary: `camera0_intensity_threshold_summary.md`, `plots/camera0_duty_detection_ci.png`, `plots/camera0_threshold_bootstrap.png`. |

## Interfaces / Contracts

```csv
# camera0_intensity_per_pulse.csv (required columns)
campaign_id,run_id,camera_index,duty,pulse_index,detected_any,detected_frames,detection_events,expected_pulses,block_id,block_order,is_dark_control,is_positive_control,acquisition_fingerprint
```

Validation contract:
1. Duty set MUST equal `{0,1,2,3,4,5,6,7,8,10,12,16,24,32,48,64,128}`.
2. Camera filter MUST keep only `camera_index=0` and matching `campaign_id`.
3. Each duty MUST have `n>=30`; target zone `50<=n<=100` SHOULD be reported.
4. Dark controls (`duty=0`) and positive controls (`16,24,32,48,64,128`) MUST be present.
5. Acquisition fingerprint MUST be constant inside campaign; drift rows are flagged non-comparable.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit (pytest) | Duty-plan completeness, replication checks, camera0/campaign filters, exclusion reasons | Add tests for complete/incomplete duty set, missing metadata, wrong index, and under-replicated duties. |
| Unit (pytest) | Wilson/logistic/bootstrap outputs | Deterministic fixtures verify CI bounds in [0,1], monotonic threshold ordering duty50<=duty90<=duty95, and bootstrap reproducibility with fixed seed. |
| Integration | End-to-end offline artifact generation | Run aggregator on fixture CSVs (no hardware) and assert all required output files + columns are produced. |

## Migration / Rollout

No migration required. Existing `webcam_intensity_*` artifacts remain historical baseline. New acceptance uses only campaign-scoped `camera0_*` outputs.

## Open Questions

- [ ] Logistic fit implementation detail: use `statsmodels`/`scipy` dependency or a pure-NumPy fallback.
- [ ] Final target replication in operations: fix at 60 per duty vs adaptive stop within 50–100 once CI width criterion is met.
- [ ] Plot style convention: keep Spanish labels (current markdown style) or switch to English for study exports.
