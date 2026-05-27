# Tasks: New Camera Mount Statistical Reconstruction Campaign

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 430–620 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (tests+runner gate) → PR 2 (batch wrapper+aggregation/reconstruction) → PR 3 (docs+ops checks) |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Add/lock production metadata contract and dark-control gate in runner with pytest RED→GREEN→REFACTOR | PR 1 | Base main; no ops execution |
| 2 | Add campaign batch wrapper + propagation to aggregation/reconstruction filters with tests | PR 2 | Depends on PR 1 |
| 3 | Update operator docs and run readiness checklist for 10x120s independent measurements | PR 3 | Depends on PR 2 |

## Phase 1: Test-First Foundation (Strict TDD)

- [x] 1.1 Create `tests/tools/test_run_dual_flash_experiment_gate.py` RED tests for missing/stale/mismatched dark-control reference, including 5-minute freshness boundary.
- [x] 1.2 Create `tests/tools/test_run_dual_flash_experiment_metadata.py` RED tests for required production fields (`campaign_id`, `mount_context`, `run_intent`, `dark_control_ref`, `run_index`, `config_fingerprint`).
- [x] 1.3 Create `tests/scripts/test_new_mount_campaign_batch.py` RED tests for batch invariants: exactly 10 runs, `run_duration_s=120`, independent run indexing, and per-run random interval bounds 1.8–2.2s.
- [x] 1.4 Create `tests/analysis/test_campaign_filtering.py` RED tests for `analysis/aggregate.py` propagation and `analysis/reconstruction.py` fail-closed behavior when campaign filter is missing.

## Phase 2: Core Implementation (Make Tests Pass)

- [x] 2.1 Update `tools/run_dual_flash_experiment.py` to enforce production preflight gate, validate dark-control freshness (5 minutes), and persist required campaign fields into `manifest.json` and `dual_summary.csv`.
- [x] 2.2 Add `scripts/new_mount_campaign_batch.sh` to initialize/update batch manifest and run exactly 10 independent production measurements at 120s each with random inter-flash intervals 1.8–2.2s.
- [x] 2.3 Update `analysis/aggregate.py` to include campaign metadata columns and campaign-scoped summary filtering.
- [x] 2.4 Update `analysis/reconstruction.py` to require explicit campaign filter for new-mount reconstruction and reject pooled cross-campaign selection.
- [x] 2.5 Update `scripts/flash_experiment.sh` and `scripts/intensity_sweep.sh` as non-production paths (`run_intent=demo|tuning`) to prevent accidental production registration.

## Phase 3: Refactor, Verification, and Documentation

- [x] 3.1 REFACTOR shared validation helpers in `tools/run_dual_flash_experiment.py` (or nearby module) without changing external behavior; keep all Phase 1 tests green.
- [x] 3.2 Run `pytest` for all new/changed tests and fix regressions until fully green.
- [x] 3.3 Update `docs/webcam_led_flash_experiment.md` with campaign protocol, dark-control gate evidence, and first-batch acceptance rules.
- [x] 3.4 Update `docs/agent_handoff_webcam_led_flash_experiment.md` checklist with run indexing, eligibility criteria, and corrective actions.

## Phase 4: Operational Measurement Execution (After Code+Docs Ready)

- [x] 4.1 Perform dry-run preflight using `scripts/new_mount_campaign_batch.sh` to verify gate rejection/approval paths and batch manifest transitions before live acquisition.
  - Follow-up bugfix applied: dark-control runs now persist gate-compatible manifest metadata so production preflight can reference real `run_intent=dark-control` output.
- [ ] 4.2 Execute first production batch (10 independent x 120s) under approved campaign ID, capturing dark-control reference and per-run interval settings.
  - Partial live evidence captured: honest `dark-control` run completed with `--preview` and `--duty 0` for campaign `new-camera-mount-20260526-phase4`, but production remained blocked before acquisition because the production gate rejected the dark-control ref with `ValueError: dark_control_ref config_fingerprint mismatch`.
  - Follow-up gate policy fix applied: dark-control comparability now uses acquisition-oriented fingerprint semantics (camera/acquisition/detector profile) so `duty=0` dark-control is accepted against `duty=1023` production when acquisition settings match.
  - Partial live evidence after fingerprint fix: new `dark-control` ref `random-train_20260526_144036` completed with `--preview`, manifest includes `acquisition_config_fingerprint=f0b3b899e9d35287`, and production runs `1/10` and `2/10` completed with preview before the third run was blocked by `ValueError: dark_control_ref is stale (older than freshness window)`.
  - Partial live evidence after batch-start freshness policy: new `dark-control` ref `random-train_20260526_154359` completed with `--preview`, manifest includes `acquisition_config_fingerprint=f0b3b899e9d35287` and was fresh, but the full batch command was terminated during the first production run before any production manifest was written (`0/10` completed).
- [ ] 4.3 Record completion evidence and eligibility status in campaign artifacts, then hand off for `sdd-apply` completion check and later `sdd-verify`.
