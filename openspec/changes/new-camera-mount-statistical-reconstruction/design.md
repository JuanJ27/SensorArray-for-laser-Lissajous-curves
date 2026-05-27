# Design: New Camera Mount Statistical Reconstruction Campaign

## Technical Approach

Implement an **operations-first campaign protocol** on top of existing dual-run tooling, without changing reconstruction algorithms yet. The design adds: (1) explicit campaign metadata in run manifests, (2) a hard dark-control gate with traceable reference, and (3) a deterministic batch manifest for `10 x 2-minute` random-train runs. This maps directly to the three delta specs and is designed for immediate field execution.

## Architecture Decisions

| Decision | Options | Tradeoff | Decision |
|---|---|---|---|
| Campaign separation key | Infer by directory/variant vs explicit `campaign_id` + `mount_context` metadata | Inference is fragile; explicit metadata is safer and queryable | Add required metadata fields in dual run manifest and downstream aggregation filters |
| Fresh dark-control rule | Leave undefined vs time+configuration bounded validity | Undefined blocks safe execution; strict rule may force reruns | Define freshness as: valid only if same `campaign_id`, `mount_context=new-camera-mount`, same acquisition config fingerprint, and captured within **5 minutes** before first production run |
| Gating location | Manual checklist only vs script-enforced preflight | Manual-only is error-prone; full refactor is heavy | Add a light preflight check in dual runner path (or campaign batch wrapper) that rejects production runs without valid dark-control reference |
| Batch orchestration | Ad-hoc repeated CLI calls vs batch manifest with completion state | Ad-hoc is fast but non-auditable; manifest is safer | Create a campaign batch manifest with planned 10 runs, per-run status, and eligibility summary |

## Data Flow

```text
Operator
  -> Dark-control run (new mount)
      -> manifest.json (dark_control=true, gate evidence)
  -> Start campaign batch (10 planned runs)
      -> preflight validates fresh dark-control
      -> run_dual_flash_experiment executes one run
      -> manifest.json (campaign_id, dark_control_ref, run_index)
      -> batch_manifest.json updates completion/eligibility
  -> analysis/aggregate.py filters by campaign_id
  -> analysis/reconstruction.py requires explicit campaign filter
```

## File Changes

| File | Action | Description |
|---|---|---|
| `tools/run_dual_flash_experiment.py` | Modify | Add required production metadata flags (`--campaign-id`, `--mount-context`, `--run-intent`, `--dark-control-ref`, `--run-index`) and gate validation before execution for production intent. Persist fields in `manifest.json` + `dual_summary.csv`. |
| `scripts/flash_experiment.sh` | Modify | Keep as non-production demo path; explicitly mark as `run-intent=demo` to avoid accidental production registration. |
| `scripts/intensity_sweep.sh` | Modify | Keep as baseline/tuning path; mark non-production and link to dark-control preparation step. |
| `scripts/new_mount_campaign_batch.sh` | Create | Safe wrapper to initialize batch manifest and execute exactly 10 production random-train runs of 120s each with fixed defaults and preflight gating. |
| `analysis/aggregate.py` | Modify | Include `campaign_id`, `mount_context`, `dark_control_ref`, `run_intent`, `run_index` in `dual_random_train_runs.csv`; support campaign-scoped summaries. |
| `analysis/reconstruction.py` | Modify | Require explicit campaign filter argument for new-mount reconstruction; fail closed when missing. |
| `docs/webcam_led_flash_experiment.md` | Modify | Add operational protocol: campaign creation, dark-control gate, and 10x2min production sequence. |
| `docs/agent_handoff_webcam_led_flash_experiment.md` | Modify | Update checklist with gate evidence, run indexing, and completion criteria for first batch eligibility. |

## Interfaces / Contracts

```json
// Added manifest contract (production runs)
{
  "campaign_id": "new-camera-mount-YYYYMMDD",
  "mount_context": "new-camera-mount",
  "run_intent": "dark-control|production|demo|tuning",
  "dark_control_ref": "<run_id of validated dark-control>",
  "run_index": 1,
  "batch_target_runs": 10,
  "run_duration_s": 120,
  "config_fingerprint": "<hash of camera+profile args>"
}
```

Dark-control freshness rule (operational):
1. `run_intent=dark-control` in referenced run.
2. Same `campaign_id` and `mount_context`.
3. Same `config_fingerprint` as production run.
4. `created_at(dark_control)` within 5 minutes before first production run (or before `batch_started_at` for an authorized continuous batch).
5. If any camera/profile parameter changes, a new dark-control is mandatory.

Batch freshness policy note:
- For ad hoc single production runs, freshness is validated against the run start timestamp.
- For `scripts/new_mount_campaign_batch.sh` continuous batches, freshness is validated once against the shared `batch_started_at` timestamp passed to each production run.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit (pytest) | Gate validator, config fingerprint, batch completion logic | Add pure-function tests for freshness pass/fail, mismatched campaign, stale timestamp, and incomplete batch (9/10). |
| Integration | Manifest-to-aggregate propagation | Run one synthetic dark-control + two production manifests and verify `dual_random_train_runs.csv` carries campaign fields and filtering works. |
| E2E (manual ops) | Real campaign execution safety | Dry-run checklist: dark-control required, production blocked without ref, batch marks complete only at 10 runs. |

## Migration / Rollout

No data migration required. Legacy runs remain readable but **not eligible** for `new-camera-mount` production reconstruction unless explicit campaign metadata exists.

## Open Questions

- [x] Dark-control freshness window confirmed by operator as 5 minutes.
- [x] First-batch intent confirmed: 10 independent 120s measurements, each using random inter-flash intervals of 1.8–2.2s for later statistical reconstruction.
