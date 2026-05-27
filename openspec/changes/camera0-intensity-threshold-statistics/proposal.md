# Proposal: Camera0 Intensity Threshold Statistics

## Intent

Re-estimate LED duty-cycle detectability near threshold using the new camera0 setup with stronger statistical confidence. Legacy camera/index-2 evidence suggests the threshold is near duty≈6, but sample size is too weak for protocol decisions.

## Scope

### In Scope
- Run a **new, campaign-separated** camera0 (`--index 0`) intensity-threshold experiment design (proposal only; no acquisition now).
- Define duty set: near-threshold `0,1,2,3,4,5,6,7,8,10,12` plus positive controls `16,24,32,48,64,128`.
- Define minimum replication: 30 pulses/duty (target 50–100), randomized/interleaved blocks, dark controls, and positive controls.
- Define analysis outputs: per-pulse table, per-duty Wilson 95% CIs, logistic + bootstrap duty50/duty90/duty95, and error-bar plots.

### Out of Scope
- Live hardware acquisition/execution in this phase.
- Merging camera0 results with legacy camera/index-2 datasets.
- Temporal/astrophoto protocol redesign (deferred until threshold uncertainty is reduced).

## Capabilities

### New Capabilities
- `camera0-intensity-threshold-statistics`: Campaign-level experiment and analysis contract to estimate camera0 duty detection thresholds with uncertainty bounds.

### Modified Capabilities
- None.

## Approach

Create a dedicated camera0 campaign workflow that preserves provenance end-to-end (capture metadata, run blocks, and analysis outputs) and enforces non-pooling with legacy datasets. Statistical deliverables prioritize interval estimates and model-based threshold summaries over single-point pass/fail claims.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/camera0-intensity-threshold-statistics/proposal.md` | New | Proposal contract for this change |
| `tools/run_led_intensity_sweep.py` | Modified (future phases) | Add campaign/camera0 metadata + randomized block support |
| `scripts/intensity_sweep.sh` | Modified (future phases) | Orchestrate camera0 campaign runs and controls |
| `data/derived/studies/` | Modified (future phases) | Store camera0-only statistical outputs |
| `data/derived/presentation/` | Modified (future phases) | Publish CI/error-bar threshold summaries |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Residual bias from order/drift effects | Med | Interleaved/randomized blocks + dark controls |
| Underpowered threshold estimates | Med | Minimum 30 pulses/duty; target 50–100 |
| Accidental camera-mixing in analysis | Med | Mandatory campaign/camera index tagging and filters |

## Rollback Plan

Revert proposal and downstream artifacts for this change folder; keep legacy datasets and scripts untouched. If later implementation introduces regressions, disable camera0 campaign path and fall back to current sweep tooling while preserving raw captured data.

## Dependencies

- Access to camera0 mount/setup and stable acquisition environment (for later phases).
- Existing sweep tooling baseline: `tools/run_led_intensity_sweep.py`, `scripts/intensity_sweep.sh`.

## Success Criteria

- [ ] Proposal explicitly enforces camera0 campaign separation from legacy data.
- [ ] Duty plan, controls, replication targets, and block randomization are fully specified.
- [ ] Statistical outputs include Wilson 95% intervals and bootstrap/logistic duty50/duty90/duty95.
- [ ] Proposal is implementation-ready for `sdd-spec` without requiring live acquisition now.
