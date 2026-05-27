# Apply Progress - new-camera-mount-statistical-reconstruction (Operational Phase 4)

## Scope

- Delivery mode: chained PR slice (`feature-branch-chain`)
- Current boundary: operational Phase 4 live dark-control completed after batch-start freshness fix; fresh production batch attempt stopped at 0/10 because the first production command was terminated before writing a production manifest
- Out of scope after this update: campaign postprocessing/reconstruction, blocked until the full 10-run production batch completes without mixing legacy data

## Completed Tasks

- [x] 1.1 RED tests for dark-control gate behavior and 5-minute freshness boundary
- [x] 1.2 RED tests for required production metadata contract fields
- [x] 1.3 RED tests for batch invariants (10 runs, 120s metadata, run indexing, interval bounds 1.8–2.2s)
- [x] 1.4 RED tests for campaign filtering propagation + reconstruction fail-closed behavior
- [x] 2.1 Implement production metadata validation + dark-control preflight + persistence in manifest/summary
- [x] 2.2 Add `scripts/new_mount_campaign_batch.sh` + helper module to initialize batch manifest and run 10 production runs with fixed bounds
- [x] 2.3 Update aggregation to propagate campaign metadata and support `campaign_id` filtering for dual random-train rows
- [x] 2.4 Update reconstruction selection path to require explicit campaign filter when `mount_context=new-camera-mount`
- [x] 2.5 Label `scripts/flash_experiment.sh` and `scripts/intensity_sweep.sh` as explicit non-production demo/tuning paths
- [x] 3.1 Refactor validation into focused helper functions
- [x] 3.2 Run pytest on all new/changed tests and reach GREEN
- [x] 3.3 Update `docs/webcam_led_flash_experiment.md` with campaign protocol, dark-control gate evidence, first-batch acceptance rules, and readiness checks (sin medición real)
- [x] 3.4 Update `docs/agent_handoff_webcam_led_flash_experiment.md` checklist with run indexing, eligibility criteria, corrective actions, and explicit non-production script boundaries
- [x] 4.1 Dry-run preflight completed without live acquisition: `bash -n scripts/new_mount_campaign_batch.sh`, missing `dark_control_ref` gate rejection, pure-helper approval gate with synthetic compatible manifest, and batch helper invariants for 10 runs, `--count 60`, `1800–2200 ms`, `run_intent=production`, campaign metadata, and dark-control reference propagation.

## Operational Phase 4 Evidence

- Campaign ID selected for preflight/live intent: `new-camera-mount-20260526-phase4`.
- Preview support update: `scripts/new_mount_campaign_batch.sh` now accepts optional `--preview` and passes it to each production run command.
- Wrapper syntax check after preview update: `bash -n scripts/new_mount_campaign_batch.sh` completed with no output.
- Fresh gate preflight command: `.venv/bin/python - <<'PY' ... validate_dark_control_gate(...) ... PY` approved a temporary fresh dark-control manifest for production-equivalent fingerprint `3b6c073f89a99177`.
- Gate rejection command: `.venv/bin/python tools/run_dual_flash_experiment.py --run-intent production --campaign-id phase4-preflight --mount-context new-camera-mount --dark-control-ref definitely_missing_dark_ref --run-index 1 random-train --count 60 --min-period-ms 1800 --max-period-ms 2200 --duration-ms 40`.
- Gate rejection result: blocked before camera/serial acquisition with `ValueError: dark_control_ref 'definitely_missing_dark_ref' does not resolve to a manifest`.
- Gate approval preflight: pure `validate_dark_control_gate(...)` call accepted a temporary compatible manifest with fingerprint `3b6c073f89a99177` and freshness under 5 minutes.
- Batch command generation preflight: `scripts.new_mount_campaign_batch.build_batch_plan(...)` and `build_run_command(...)` verified 10 production runs, `run_duration_s=120`, `--count 60`, `--min-period-ms 1800`, `--max-period-ms 2200`, `mount_context=new-camera-mount`, `run_index=1..10`, and `dark_control_ref` propagation.
- Live acquisition was not started because the current runner cannot honestly produce a compatible fresh dark-control manifest for production gating: `write_manifest(...)` only persists campaign/gate fields when `production_metadata` is present, and `production_metadata` is only created for `run_intent=production`. A `run_intent=dark-control` execution therefore would not emit top-level `run_intent=dark-control`, `campaign_id`, `mount_context`, or `config_fingerprint` required by `validate_dark_control_gate(...)`.
- A manual minimal manifest was not created because no actual compatible dark-control output existed to bind it to, and using `duty=0` for a dark run would change `config_fingerprint` relative to the required production `duty=1023` configuration.
- Live dark-control command executed after manifest blocker fix: `.venv/bin/python tools/run_dual_flash_experiment.py --preview --run-intent dark-control --campaign-id new-camera-mount-20260526-phase4 --mount-context new-camera-mount --run-index 0 random-train --count 60 --min-period-ms 1800 --max-period-ms 2200 --duration-ms 40 --duty 0`.
- Live dark-control output: `data/dual_experiments/random-train_20260526_143212/manifest.json`; dark-control ref `random-train_20260526_143212`; `config_fingerprint=01f9ecc22677bedb`; webcam video `data/dual_experiments/random-train_20260526_143212/webcam_capture.avi`; summary `data/dual_experiments/random-train_20260526_143212/dual_summary.csv`.
- Preview status: `--preview` was passed; OpenCV emitted Qt Wayland/font warnings but the run completed. The tool does not expose an operator acceptance prompt, so visual acceptability could not be programmatically confirmed.
- Production gate check command: `.venv/bin/python tools/run_dual_flash_experiment.py --preview --run-intent production --campaign-id new-camera-mount-20260526-phase4 --mount-context new-camera-mount --dark-control-ref random-train_20260526_143212 --run-index 1 random-train --count 60 --min-period-ms 1800 --max-period-ms 2200 --duration-ms 40`.
- Production gate check result (before fix): blocked before production acquisition with `ValueError: dark_control_ref config_fingerprint mismatch` because the honest dark-control used `--duty 0` while production defaults to `--duty 1023` and `duty` was part of gate comparability.
- Production batch completed: `0/10`. Aggregation/reconstruction were not run because no production run completed for this campaign.

## Operational Phase 4 Evidence After Fingerprint Fix

- Campaign ID: `new-camera-mount-20260526-phase4`.
- Fresh dark-control command: `.venv/bin/python tools/run_dual_flash_experiment.py --preview --run-intent dark-control --campaign-id new-camera-mount-20260526-phase4 --mount-context new-camera-mount --run-index 0 random-train --count 60 --min-period-ms 1800 --max-period-ms 2200 --duration-ms 40 --duty 0`.
- Fresh dark-control output: `data/dual_experiments/random-train_20260526_144036/manifest.json`; dark-control ref `random-train_20260526_144036`; webcam video `data/dual_experiments/random-train_20260526_144036/webcam_capture.avi`; summary `data/dual_experiments/random-train_20260526_144036/dual_summary.csv`.
- Manifest freshness check command: `.venv/bin/python - <<'PY' ... inspect data/dual_experiments/random-train_20260526_144036/manifest.json ... PY`.
- Manifest freshness result: `created_at=2026-05-26T14:43:01`, `age_seconds=9.2`, `within_5_minutes=True`, `run_intent=dark-control`, `campaign_id=new-camera-mount-20260526-phase4`, `mount_context=new-camera-mount`, `config_fingerprint=01f9ecc22677bedb`, `acquisition_config_fingerprint=f0b3b899e9d35287`.
- Batch command attempted directly: `scripts/new_mount_campaign_batch.sh new-camera-mount-20260526-phase4 random-train_20260526_144036 --preview`.
- Direct batch command result: failed before acquisition with `zsh:1: permission denied: scripts/new_mount_campaign_batch.sh` because the wrapper is not executable.
- Batch command executed via bash: `bash scripts/new_mount_campaign_batch.sh new-camera-mount-20260526-phase4 random-train_20260526_144036 --preview`.
- Preview status: `--preview` was passed to dark-control and production runs; OpenCV emitted Qt Wayland/font warnings but the completed runs continued and wrote video/metrics outputs.
- Production run 1 completed: `data/dual_experiments/random-train_20260526_144326/manifest.json`, `data/dual_experiments/random-train_20260526_144326/webcam_capture.avi`, `data/dual_experiments/random-train_20260526_144326/dual_summary.csv`.
- Production run 2 completed: `data/dual_experiments/random-train_20260526_144551/manifest.json`, `data/dual_experiments/random-train_20260526_144551/webcam_capture.avi`, `data/dual_experiments/random-train_20260526_144551/dual_summary.csv`.
- Production batch completed: `2/10`.
- Batch blocker before run 3: `ValueError: dark_control_ref is stale (older than freshness window)` raised by `validate_dark_control_gate(...)`.
- Aggregation/reconstruction were not run because the required 10 production runs did not complete; this avoids mixing partial campaign data with legacy data.

## Operational Phase 4 Follow-up Policy Fix (Authorized Option 1)

- Safety policy update implemented: dark-control freshness now anchors to batch start for continuous campaign batches, while ad hoc single production runs keep per-run freshness validation.
- Runner update: `tools/run_dual_flash_experiment.py` accepts optional `--batch-started-at` (ISO timestamp) and `validate_dark_control_gate(...)` uses this timestamp when provided; otherwise behavior remains per-run.
- Batch wrapper update: `scripts/new_mount_campaign_batch.sh` captures one `BATCH_STARTED_AT` timestamp before run loop and passes it unchanged to all 10 production runs.
- Helper contract update: `scripts/new_mount_campaign_batch.py::build_run_command(...)` now includes `--batch-started-at`.
- Regression coverage added:
  - stale-by-run but fresh-at-batch-start passes;
  - stale-at-batch-start fails;
  - existing ad hoc per-run stale checks remain enforced.
- Phase 4 production status remains unchanged: still partial (`2/10`) and **not** marked complete in tasks.

## Operational Phase 4 Live Attempt After Batch-Start Freshness Fix

- Campaign ID: `new-camera-mount-20260526-phase4`.
- Fresh dark-control command: `.venv/bin/python tools/run_dual_flash_experiment.py --preview --run-intent dark-control --campaign-id new-camera-mount-20260526-phase4 --mount-context new-camera-mount --run-index 0 random-train --count 60 --min-period-ms 1800 --max-period-ms 2200 --duration-ms 40 --duty 0`.
- Fresh dark-control output: `data/dual_experiments/random-train_20260526_154359/manifest.json`; dark-control ref `random-train_20260526_154359`; webcam video `data/dual_experiments/random-train_20260526_154359/webcam_capture.avi`; summary `data/dual_experiments/random-train_20260526_154359/dual_summary.csv`.
- Manifest freshness check command: `.venv/bin/python - <<'PY' ... inspect data/dual_experiments/random-train_20260526_154359/manifest.json ... PY`.
- Manifest freshness result: `created_at=2026-05-26T15:46:09`, `age_seconds=9.0`, `within_5_minutes=True`, `run_intent=dark-control`, `campaign_id=new-camera-mount-20260526-phase4`, `mount_context=new-camera-mount`, `config_fingerprint=01f9ecc22677bedb`, `acquisition_config_fingerprint=f0b3b899e9d35287`.
- Batch command attempted: `bash scripts/new_mount_campaign_batch.sh new-camera-mount-20260526-phase4 random-train_20260526_154359 --preview`.
- Batch initialization output: `Initialized batch manifest: data/dual_experiments/new_mount_campaigns/new-camera-mount-20260526-phase4/batch_manifest.json`.
- Batch blocker: first production command was terminated before any production manifest was written: `Terminated                 python tools/run_dual_flash_experiment.py $PREVIEW_ARG --run-intent production --campaign-id "$CAMPAIGN_ID" --mount-context new-camera-mount --dark-control-ref "$DARK_CONTROL_REF" --batch-started-at "$BATCH_STARTED_AT" --run-index "$run_index" random-train --min-period-ms 1800 --max-period-ms 2200 --count 60 --duration-ms 40`.
- Output inspection command: `.venv/bin/python - <<'PY' ... count production manifests with campaign_id=new-camera-mount-20260526-phase4 and dark_control_ref=random-train_20260526_154359 ... PY`.
- Output inspection result: `production_runs_for_dark_ref=0`; batch manifest exists at `data/dual_experiments/new_mount_campaigns/new-camera-mount-20260526-phase4/batch_manifest.json` with `batch_created_at=2026-05-26T15:46:23` and `target=10`.
- Preview status: `--preview` was passed to dark-control and the attempted production batch; the dark-control preview path ran with OpenCV Qt Wayland/font warnings and completed. The production preview attempt did not complete because the first production process was terminated.
- Production batch completed for this fresh attempt: `0/10`.
- Aggregation/reconstruction were not run because the required complete 10-run production batch did not complete; this avoids mixing this failed attempt with legacy partial runs.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/tools/test_run_dual_flash_experiment_gate.py` | Unit | N/A (new tests) | ✅ Wrote failing tests first (missing function failures) | ✅ `pytest tests/tools/test_run_dual_flash_experiment_gate.py tests/tools/test_run_dual_flash_experiment_metadata.py` | ✅ 4 cases (missing ref, stale, mismatched mount, exact 5-min boundary) | ✅ Extracted gate helpers in runner |
| 1.2 | `tests/tools/test_run_dual_flash_experiment_metadata.py` | Unit | N/A (new tests) | ✅ Wrote failing tests first (missing function failures) | ✅ `pytest tests/tools/test_run_dual_flash_experiment_gate.py tests/tools/test_run_dual_flash_experiment_metadata.py` | ✅ 5 cases (required fields, run_index, positive happy path) | ✅ Shared metadata helpers extracted |
| 2.1 | `tests/tools/test_run_dual_flash_experiment_gate.py`, `tests/tools/test_run_dual_flash_experiment_metadata.py` | Unit | N/A (new behavior) | ✅ Existing RED from 1.1/1.2 drove implementation | ✅ Same pytest command passed 9/9 | ✅ Contract and gate behaviors covered by independent cases | ✅ No behavior change after helper extraction |
| 3.1 | Same as above | Unit | ✅ Baseline before refactor: 9/9 passing | ✅ Approval-style guard used by existing tests | ✅ Post-refactor: 9/9 passing | ➖ Covered by prior cases | ✅ `_require_non_empty`, fingerprint and gate helpers |
| 1.3 | `tests/scripts/test_new_mount_campaign_batch.py` | Unit | N/A (new tests) | ✅ Wrote failing tests first (module import failed) | ✅ `pytest tests/scripts/test_new_mount_campaign_batch.py` | ✅ 3 cases (10 runs, 120s+interval bounds, command metadata) | ✅ Shared constants + command builder extracted |
| 1.4 | `tests/analysis/test_campaign_filtering.py` | Unit | N/A (new tests) | ✅ Wrote failing tests first (missing API/function) | ✅ `pytest tests/analysis/test_campaign_filtering.py` | ✅ 2 cases (campaign filter propagation + missing filter fail-closed) | ✅ Kept checks in pure helpers |
| 2.2 | `tests/scripts/test_new_mount_campaign_batch.py` | Unit | N/A (new module/script) | ✅ RED from 1.3 drove implementation | ✅ Same pytest file passed 3/3 | ✅ Batch plan + command assertions cover distinct paths | ✅ Constants centralized for wrapper + helper |
| 2.3 | `tests/analysis/test_campaign_filtering.py` | Unit | N/A (new behavior) | ✅ RED from 1.4 drove implementation | ✅ Same pytest file passed 2/2 | ✅ Verified filter excludes legacy campaign row | ✅ Minimal signature extension on aggregator |
| 2.4 | `tests/analysis/test_campaign_filtering.py` | Unit | ✅ Baseline before edits: 14/14 passing related suite | ✅ RED from 1.4 drove implementation | ✅ Related suite returned 14/14 passing | ✅ Missing-filter rejection and positive filter path separated | ✅ Fail-closed helper isolated in reconstruction |
| 3.2 | `tests/tools/test_run_dual_flash_experiment_gate.py`, `tests/tools/test_run_dual_flash_experiment_metadata.py`, `tests/scripts/test_new_mount_campaign_batch.py`, `tests/analysis/test_campaign_filtering.py` | Unit | ✅ 14/14 baseline retained | ✅ N/A (execution/verification task) | ✅ `pytest ...` => 14/14 passing | ➖ N/A | ➖ N/A |
| 2.5 | `tests/scripts/test_non_production_script_labels.py` | Unit | ✅ Scripts existed; syntax check baseline with `bash -n` | ✅ Wrote tests first for explicit `[NON-PRODUCTION]` + intent labels | ✅ `pytest tests/scripts/test_non_production_script_labels.py` (2/2) | ✅ Demo and tuning scripts validated independently | ✅ No behavior change in command paths; explicit stderr labeling only |
| 3.3 | `tests/docs/test_new_mount_campaign_readiness_docs.py` | Unit | ✅ Guide existed; assertions target required protocol content | ✅ Added failing doc-contract assertions first | ✅ `pytest tests/docs/test_new_mount_campaign_readiness_docs.py` (2/2) | ✅ Coverage includes gate freshness, batch acceptance, readiness commands | ✅ Section structured to separate readiness vs Phase 4 live execution |
| 3.4 | `tests/docs/test_new_mount_campaign_readiness_docs.py` | Unit | ✅ Handoff checklist existed; assertions target governance additions | ✅ Added failing handoff assertions before doc edits | ✅ Same pytest file stayed green (2/2) | ✅ Checklist + governance section validated as separate paths | ✅ Clarified corrective action boundary and operational handoff |

## Test Summary

- Total tests written: 18
- Total tests passing: 18
- Layers used: Unit (18), Integration (0), E2E (0)
- Approval tests: None (no legacy behavior lock needed beyond targeted unit coverage)
- Pure helpers created: 8 (`_require_non_empty`, `build_config_fingerprint`, `validate_production_metadata`, `_resolve_dark_control_manifest`, `validate_dark_control_gate`, `build_batch_plan`, `build_run_command`, `require_campaign_filter_for_new_mount`)

## Notes

- Dark-control freshness is enforced as `<= 5 minutes` before production start.
- Production gate is fail-closed: missing/mismatched/stale dark-control reference blocks execution.
- Phase 4 blocker fix (2026-05-26): `run_intent=dark-control` now persists gate-compatible metadata (`run_intent`, `campaign_id`, `mount_context`, `run_index`, `config_fingerprint`) in `manifest.json`, so `validate_dark_control_gate(...)` can resolve a real dark-control run produced by the runner itself.
- Fingerprint policy correction (2026-05-26 live blocker): gate comparability now prefers `acquisition_config_fingerprint` (camera/acquisition/detector profile) and falls back to legacy `config_fingerprint` for backward compatibility; this allows honest dark-control `--duty 0` to satisfy production gating with `--duty 1023` when acquisition settings match.
- Required metadata contract fields are persisted in both `manifest.json` and `dual_summary.csv` for production runs.
- Batch wrapper hard-codes first-batch constraints (10 runs, random-train with 1.8–2.2s intervals) and initializes campaign batch manifest before execution.
- Follow-up bugfix (measurement duration ambiguity): batch execution count was corrected from `30` to `60` flashes per run in both helper and shell wrapper so each run targets ~120 seconds at 1.8–2.2 s random intervals.
- Aggregation now propagates `campaign_id`, `mount_context`, `run_intent`, `dark_control_ref`, `run_index` and supports campaign-scoped dual-run selection.
- Reconstruction now fails closed for new-mount records when campaign filter is omitted.
- Legacy demo/tuning scripts are now explicitly marked as non-production in stderr output to reduce accidental misuse.
- Readiness docs now include no-acquisition check commands and an explicit boundary: Phase 4 is still pending for live measurements.
