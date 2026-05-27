# Proposal: Astrophoto Temporal Accumulation Protocol

## Intent

Replace the invalid sub-frame pulse-reconstruction claim with a defensible model: webcam outputs are temporal integrations over windows much longer than short LED pulses, so evidence must come from multi-event accumulation and SNR gains (astrophoto/stacking analogy).

## Scope

### In Scope
- Define a standalone campaign protocol for temporal accumulation, separated from intensity-threshold statistics and from prior Gaussian sub-frame reconstruction claims.
- Define four experimental phases: dark control, pulse-duration exploration, high-intensity short-pulse accumulation, minimum-intensity short-pulse accumulation.
- Define analysis deliverables: stacked/averaged frames, SNR vs dark baseline, bootstrap confidence intervals by run/event, and false-positive reporting.
- Define dependency boundary: minimum-intensity short-pulse phase consumes the future camera0 minimum-intensity estimate as an input, but does not compute it here.
- Define documentation and acceptance criteria only (no acquisition execution in this phase).

### Out of Scope
- Claiming sub-frame pulse shape (e.g., Gaussian profile) from webcam-only data.
- Estimating pulse duration directly from webcam frames without external timing instrumentation.
- Running live acquisition, hardware reconfiguration, or producing final scientific conclusions in proposal phase.
- Mixing this campaign’s results with camera0 intensity-threshold campaign statistics.

## Capabilities

### New Capabilities
- `astrophoto-temporal-accumulation-protocol`: Protocol and analysis contract for event stacking/averaging under temporal integration constraints.
- `campaign-separation-governance`: Rules preventing cross-claim contamination between threshold statistics, legacy reconstruction hypotheses, and accumulation experiments.

### Modified Capabilities
- None.

## Approach

Use a campaign-first specification: each phase has fixed inputs, outputs, and quality checks; analysis is based on accumulation statistics (not intra-frame structure). The minimum-intensity branch remains blocked until threshold study publishes a stable estimate.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/astrophoto-temporal-accumulation-protocol/` | New | Proposal now; later specs/design/tasks for this change. |
| `openspec/changes/astrophoto-temporal-accumulation-protocol/specs/` | New | Delta specs to define protocol, phase boundaries, and acceptance scenarios. |
| `notebooks/` | Modified (planned) | Analysis notebooks for stacking, SNR, bootstrap CIs, false positives. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Campaigns get mixed in analysis narrative | Med | Enforce explicit dataset tags and separate reporting sections by campaign. |
| Overclaiming temporal resolution from integrated frames | High | Hard out-of-scope guard in specs and review checklist. |
| Minimum-intensity input delayed | Med | Keep that phase blocked and proceed with dark/high-intensity branches first. |

## Rollback Plan

If downstream evidence or instrumentation assumptions change, archive this change as superseded and revert to a neutral protocol-only baseline (dark + high-intensity accumulation) without minimum-intensity branch.

## Dependencies

- Future output from `camera0-intensity-threshold-statistics`: minimum intensity estimate and uncertainty bounds.

## Success Criteria

- [ ] Proposal states integrated-signal/SNR claim and explicitly rejects sub-frame pulse-shape reconstruction.
- [ ] Scope enforces campaign separation from threshold statistics and legacy reconstruction claims.
- [ ] Four-phase experiment plan and analysis deliverables are fully specified for sdd-spec.
- [ ] No live acquisition activity is required or implied in proposal artifacts.
