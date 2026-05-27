# Apply Progress — camera0-intensity-threshold-statistics (PR1+PR2+PR3 cumulative)

## Scope Boundary

- Chain mode: `feature-branch-chain`
- Current slice: `PR3 / Work Unit 3`
- Implemented boundary: operational live-acquisition checklist/help gates + acceptance checklist template
- Explicitly excluded: hardware execution and live acquisition runtime

## Completed Tasks

- [x] 1.1 Add required constants/contracts (duty set, fixed 60 pulses per duty, controls, required columns).
- [x] 1.3 Add plan/metadata validation helpers (campaign id, camera0 filter, acquisition fingerprint consistency, exclusion reasons).
- [x] 2.1 RED tests for plan validation and fixed pulses/interleaving checks.
- [x] 2.2 RED tests for campaign/camera filtering and exclusion reasons.
- [x] 2.3 RED tests for Wilson bounds + monotonic thresholds + bootstrap reproducibility.
- [x] 2.4 GREEN implementation in `analysis/aggregate.py` and `analysis/uncertainty.py` (NumPy-first).
- [x] 2.5 REFACTOR cleanup (shared constants/helpers, deterministic bootstrap seed default).
- [x] 1.2 Add offline plan-generation mode (`--emit-plan-only`) producing `data/derived/studies/camera0_intensity_campaign_plan.csv`.
- [x] 2.6 Add `tests/test_camera0_artifact_generation.py` for outputs/columns and Spanish summary label checks.
- [x] 3.1 Update sweep CLI for required `--campaign-id`, `--run-intent`, explicit index contract, and structured metadata output.
- [x] 3.2 Update `scripts/intensity_sweep.sh` camera0 threshold wrapper with safe default plan/preflight path and live execution gate.
- [x] 3.3 Add offline artifact writer for camera0 outputs (`per_pulse`, `wilson`, `thresholds`, `validation_report`).
- [x] 4.1 Define live campaign execution task in `scripts/intensity_sweep.sh` usage/help with preview plan, preflight checks, and explicit operator confirmation gate (`OPERADOR_CONFIRMA_LIVE=SI`).
- [x] 4.2 Add acceptance checklist template in `data/derived/presentation/camera0_intensity_threshold_summary.md` with Spanish labels and required artifact presence.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 + 2.1 | `tests/test_camera0_plan_validation.py` | Unit | ⚠️ `pytest` baseline failed from pre-existing `hardware/latency_test.py` import (`machine`) | ✅ Written first (missing symbols) | ✅ Pass | ✅ 2 scenarios (complete/incomplete plan) | ✅ constants+helper cleanup |
| 1.3 + 2.2 | `tests/test_camera0_filtering.py` | Unit | ⚠️ Same pre-existing baseline failure | ✅ Written first (missing symbol) | ✅ Pass | ✅ 2 scenarios (wrong-camera/campaign + missing metadata/drift) | ✅ canonical fingerprint mode logic |
| 2.3 + 2.4 + 2.5 | `tests/test_wilson_and_thresholds.py` | Unit | ⚠️ Same pre-existing baseline failure | ✅ Written first (missing symbols) | ✅ Pass | ✅ 3 scenarios (bounds, monotonic thresholds, deterministic bootstrap) | ✅ extracted fit/threshold helpers + default seed |
| 1.2 + 3.1 | `tests/test_camera0_artifact_generation.py::test_emit_plan_only_writes_camera0_campaign_plan_with_fixed_60` | Unit | ✅ targeted baseline green (PR1 tests) | ✅ Written first for plan metadata/path contract | ✅ Pass | ✅ fixed-60 + per-duty count checks | ✅ lazy serial import + package import fallback |
| 2.6 + 3.3 | `tests/test_camera0_artifact_generation.py::test_generate_camera0_threshold_artifacts_writes_required_csvs_and_spanish_summary` | Unit | ✅ targeted baseline green (PR1 tests) | ✅ Written first for artifact set/columns/Spanish label | ✅ Pass | ✅ 4 artifact files + required-column assertions | ✅ extracted camera0 artifact writer in `analysis/aggregate.py` |
| 3.2 | `bash -n scripts/intensity_sweep.sh` | Unit | N/A (shell wrapper) | ✅ Safety gates specified before live path | ✅ Pass (`bash -n`) | ➖ Single (structural wrapper gate) | ✅ clearer mode split (`plan|preflight|live`) |
| 4.1 | `tests/docs/test_camera0_threshold_ops_contract.py::test_intensity_sweep_wrapper_documents_preview_preflight_and_confirmation_gates` | Unit | ✅ targeted baseline RED then GREEN on wrapper contract | ✅ Written first (usage/help + live gate contract absent) | ✅ Pass | ✅ preview + preflight + explicit live confirmation gate | ✅ usage/help wording aligned with safeguards (`--index 0`, campaign id, no pooling legado) |
| 4.2 | `tests/docs/test_camera0_threshold_ops_contract.py::test_camera0_threshold_summary_template_includes_acceptance_checklist_and_required_artifacts` | Unit | ✅ targeted baseline RED then GREEN on template contract | ✅ Written first (summary template missing) | ✅ Pass | ✅ checklist labels + required artifacts + plot entries | ✅ concise Spanish acceptance template with explicit completion fields |
| verify-fix | `tests/test_camera0_artifact_generation.py::test_generate_camera0_threshold_artifacts_writes_required_csvs_and_spanish_summary` | Unit | ✅ verify found missing plot outputs | ✅ Test strengthened for actual PNGs + summary plot references | ✅ Pass | ✅ CI plot + bootstrap plot + Spanish summary | ✅ plot generation isolated in camera0 artifact path |

## Tests Executed

1. `pytest` (legacy baseline in PR1) → failed due to pre-existing `hardware/latency_test.py` import (`machine`).
2. `pytest tests/test_camera0_artifact_generation.py tests/test_camera0_plan_validation.py tests/test_camera0_filtering.py tests/test_wilson_and_thresholds.py` → `9 passed`.
3. `python -m py_compile tools/run_led_intensity_sweep.py analysis/aggregate.py analysis/uncertainty.py` → pass.
4. `bash -n scripts/intensity_sweep.sh` → pass.
5. `pytest tests/docs/test_camera0_threshold_ops_contract.py` → `2 passed`.
6. Verify-fix targeted suite: `pytest tests/test_camera0_artifact_generation.py tests/test_camera0_plan_validation.py tests/test_camera0_filtering.py tests/test_wilson_and_thresholds.py tests/docs/test_camera0_threshold_ops_contract.py` → `11 passed`.
7. Verify-fix syntax checks: `python -m py_compile tools/run_led_intensity_sweep.py analysis/aggregate.py analysis/uncertainty.py` and `bash -n scripts/intensity_sweep.sh` → pass.

## Verify Fix Notes

- Added actual offline plot generation for `camera0_duty_detection_ci.png` and `camera0_threshold_bootstrap.png` in the camera0 threshold artifact writer.
- Added generated Spanish summary references to both plot files so the full output package is behaviorally proven.
- No hardware or live acquisition was executed.

## Remaining Tasks (for later PR slices)

- [x] None — all tasks in this change are completed.
