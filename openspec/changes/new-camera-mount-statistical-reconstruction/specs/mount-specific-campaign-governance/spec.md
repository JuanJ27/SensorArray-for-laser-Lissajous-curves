# Mount-Specific Campaign Governance Specification

## Purpose

Prevent any silent mixing between legacy camera-mount campaigns and the new camera-mount campaign during acquisition registration and reconstruction input selection.

## Requirements

### Requirement: Explicit Mount Campaign Identity

The system MUST register every run with an explicit campaign identifier that distinguishes `new-camera-mount` from legacy campaigns, and SHALL reject unlabeled production runs.

#### Scenario: New mount run is registered with explicit identity

- GIVEN an operator starts a production-intent run for the new mount
- WHEN run metadata is recorded
- THEN metadata includes campaign identifier `new-camera-mount`
- AND metadata includes mount context value distinct from legacy campaigns

#### Scenario: Unlabeled production run is blocked

- GIVEN an operator starts a production-intent run without campaign identifier
- WHEN the run registration step validates metadata
- THEN registration is rejected
- AND the run is marked non-compliant for reconstruction input eligibility

### Requirement: Reconstruction Input Separation by Campaign

Reconstruction input selection MUST filter by explicit campaign identifier and MUST NOT include legacy campaign runs when `new-camera-mount` reconstruction is requested.

#### Scenario: New campaign reconstruction excludes legacy runs

- GIVEN a dataset containing legacy and `new-camera-mount` run manifests
- WHEN reconstruction inputs are selected for `new-camera-mount`
- THEN only `new-camera-mount` runs are included
- AND no legacy run appears in the selected input set

#### Scenario: Missing campaign filter fails safely

- GIVEN reconstruction input selection is invoked without campaign filter
- WHEN selection policy is evaluated
- THEN the operation is rejected
- AND no pooled cross-campaign dataset is produced
