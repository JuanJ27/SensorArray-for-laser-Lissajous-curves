# Fixed Statistical Batch Acquisition Specification

## Purpose

Define and enforce the first production statistical batch for the new camera mount as exactly 10 dual runs, each lasting 2 minutes, with compliant campaign metadata.

## Requirements

### Requirement: Fixed First Batch Cardinality and Duration

The first production batch for `new-camera-mount` MUST contain exactly 10 completed dual runs, and each run MUST have configured duration of 2 minutes.

#### Scenario: Batch completes at exact target size

- GIVEN batch initialization for first `new-camera-mount` production campaign
- WHEN runs are executed and counted
- THEN completion status is reached only at 10 completed dual runs
- AND each completed run has 2-minute duration metadata

#### Scenario: Underfilled batch cannot be marked complete

- GIVEN only 9 completed dual runs are registered
- WHEN completion status is requested
- THEN batch is marked incomplete
- AND reconstruction eligibility for first-batch claim is denied

### Requirement: First-Batch Hygiene and Eligibility

The system SHALL mark first-batch reconstruction eligibility only when campaign separation and dark-control gate evidence are both present for all 10 runs.

#### Scenario: Eligible first batch passes hygiene checks

- GIVEN 10 dual runs at 2 minutes each are registered under `new-camera-mount`
- WHEN hygiene checks evaluate campaign identity and dark-control references
- THEN the batch is marked reconstruction-eligible
- AND eligibility state is recorded in the batch manifest

#### Scenario: Hygiene failure blocks eligibility

- GIVEN one or more runs in the 10-run batch lack campaign identity or dark-control reference
- WHEN hygiene checks are executed
- THEN the batch is marked not eligible
- AND corrective rerun or metadata remediation is required
