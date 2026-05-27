# Proposal: New Camera Mount Statistical Reconstruction Campaign

## Intent

Define a mount-specific acquisition campaign so reconstruction inputs from the **new camera mount** are not mixed with legacy geometry runs. Prioritize a dark-control baseline and a fixed first statistical batch.

## Scope

### In Scope
- Define campaign identity and separation rules between legacy mount and new mount runs.
- Define a required dark-control baseline gate before production acquisitions.
- Define the first production batch as **10 random-train dual runs of 2 minutes each** under fixed settings.
- Align operational docs/scripts only where needed to execute and record this campaign reliably.

### Out of Scope
- Rewriting reconstruction algorithms or changing selection logic in this phase.
- Broad detector architecture refactors beyond campaign baseline/tuning procedure.
- Publishing cross-campaign performance claims before new batch completion.

## Capabilities

### New Capabilities
- `mount-specific-campaign-governance`: enforce explicit campaign labeling and separation for acquisition/reconstruction inputs.
- `dark-control-gated-acquisition`: require validated dark-control baseline before any statistical production run.
- `fixed-statistical-batch-acquisition`: run and register a deterministic initial batch of 10 × 2-minute dual captures.

### Modified Capabilities
- None.

## Approach

Use an operations-first protocol (from exploration approach 2+3):
1) run dark-control + detector re-baseline for the new mount, then
2) execute the fixed 10×2-minute batch with explicit campaign metadata.
Only update scripts/docs required to prevent accidental old/new campaign mixing.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `docs/webcam_led_flash_experiment.md` | Modified | Add mount-distinction, dark-control gate, and 10×2-min campaign workflow. |
| `docs/agent_handoff_webcam_led_flash_experiment.md` | Modified | Update operator checklist and campaign labeling rules. |
| `scripts/flash_experiment.sh` | Modified | Align runtime defaults/flags with new campaign execution requirements. |
| `scripts/intensity_sweep.sh` | Modified | Align baseline sweep invocation with new mount re-baseline step. |
| `tools/run_dual_flash_experiment.py` | Modified | Ensure campaign metadata and run manifest separation are explicit. |
| `analysis/reconstruction.py` | Modified | Guard against implicit pooling across legacy/new mount campaign datasets. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Legacy/new run mixing | Med | Mandatory campaign identifiers and reconstruction input filtering rules. |
| Baseline drift after mount change | Med | Dark-control gate required before production batch. |
| Incomplete statistical coverage | Low/Med | Fixed 10-run plan and run-count completion checks. |

## Rollback Plan

If protocol updates cause unreliable acquisitions, revert docs/script defaults to prior behavior, mark all new-mount runs as isolated experimental data, and pause reconstruction updates until baseline is revalidated.

## Dependencies

- Availability of the new mount hardware setup and stable camera device selection.
- Operator execution of dark-control and baseline steps before batch start.

## Success Criteria

- [ ] New campaign definition explicitly distinguishes mount context from legacy campaigns.
- [ ] Dark-control baseline is documented and treated as a hard gate.
- [ ] First batch plan is fixed to **10 runs × 2 minutes** and executed with campaign metadata.
- [ ] Reconstruction inputs can be filtered to new campaign only (no silent cross-campaign pooling).
