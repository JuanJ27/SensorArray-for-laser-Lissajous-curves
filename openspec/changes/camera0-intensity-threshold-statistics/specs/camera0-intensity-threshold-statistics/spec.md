# Camera0 Intensity Threshold Statistics Specification

## Purpose

Define a camera0-only experimental and analysis contract to estimate LED duty detectability near threshold with uncertainty bounds, while preventing contamination from legacy or wrong-camera data.

## Requirements

### Requirement: Camera0 Campaign Separation and Provenance

The system MUST treat `camera0-intensity-threshold-statistics` as a distinct campaign and MUST NOT pool its analysis with legacy/index-2 or non-camera0 records.

#### Scenario: Camera0-only records are accepted for threshold analysis

- GIVEN a dataset tagged with campaign `camera0-intensity-threshold-statistics` and camera index `0`
- WHEN threshold analysis input is validated
- THEN records are accepted into the camera0 analysis cohort
- AND cohort provenance is preserved in analysis outputs

#### Scenario: Wrong-camera or legacy records are excluded

- GIVEN records from legacy campaigns, index `2`, or missing/incorrect camera metadata
- WHEN threshold analysis input is validated
- THEN those records are excluded from the camera0 cohort
- AND the exclusion reason is reported

### Requirement: Duty Plan Coverage

The experiment plan MUST include near-threshold duties `0,1,2,3,4,5,6,7,8,10,12` and positive-control duties `16,24,32,48,64,128`.

#### Scenario: Duty plan is complete

- GIVEN a declared duty plan for this capability
- WHEN duty values are checked against required sets
- THEN all near-threshold and positive-control duties are present

#### Scenario: Incomplete duty plan is rejected

- GIVEN a declared duty plan missing one or more required values
- WHEN duty values are validated
- THEN the plan is marked non-compliant

### Requirement: Replication and Block Randomization

Each required duty MUST have at least 30 pulses, SHOULD target 50–100 pulses, and SHALL be executed in randomized/interleaved blocks.

#### Scenario: Compliant replication with randomized blocks

- GIVEN acquisition design for all required duties
- WHEN replication and block ordering are evaluated
- THEN each duty has >=30 planned pulses
- AND block order is randomized/interleaved across duties

#### Scenario: Under-replicated duty is flagged

- GIVEN one or more duties planned with fewer than 30 pulses
- WHEN replication checks are executed
- THEN the design is marked non-compliant
- AND affected duties are identified

### Requirement: Control Policy and Fixed Acquisition Configuration

The campaign MUST include dark controls and positive controls, and MUST use a fixed camera/acquisition configuration across campaign runs.

#### Scenario: Controls and fixed config are present

- GIVEN campaign metadata and run configuration declarations
- WHEN control and configuration checks are executed
- THEN dark and positive controls are present
- AND camera/acquisition configuration is constant across runs

#### Scenario: Configuration drift invalidates comparability

- GIVEN run declarations with camera/acquisition parameter drift
- WHEN consistency checks are executed
- THEN the affected runs are marked non-comparable for campaign-level threshold claims

### Requirement: Statistical Analysis Outputs

The analysis output MUST include a per-pulse table, per-duty Wilson 95% confidence intervals, logistic and bootstrap estimates for duty50/duty90/duty95, and plots with error bars.

#### Scenario: Full output package is produced

- GIVEN a compliant camera0 campaign dataset
- WHEN statistical analysis is executed
- THEN outputs include the required per-pulse and per-duty tables
- AND duty50/duty90/duty95 estimates and error-bar plots are produced

#### Scenario: Missing required artifact fails acceptance

- GIVEN an analysis run missing one or more required artifacts
- WHEN output acceptance checks are executed
- THEN the run is marked incomplete
- AND missing artifacts are reported

### Requirement: Spec-Phase Non-Execution Boundary

During the spec phase, the workflow MUST NOT execute live acquisition or hardware actions; it SHALL define requirements only.

#### Scenario: Spec artifacts are produced without hardware execution

- GIVEN the capability is in spec phase
- WHEN artifacts are generated
- THEN only specification artifacts are created
- AND no live acquisition execution is triggered
