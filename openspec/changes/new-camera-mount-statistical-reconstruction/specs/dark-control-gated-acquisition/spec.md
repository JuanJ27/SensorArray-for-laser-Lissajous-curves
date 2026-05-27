# Dark-Control Gated Acquisition Specification

## Purpose

Require a fresh dark-control baseline for the new camera mount before any production statistical acquisition is allowed.

## Requirements

### Requirement: Mandatory Fresh Dark-Control Gate

The system MUST require a validated dark-control run for `new-camera-mount` before starting any production statistical run, and MUST treat stale or missing dark-control evidence as a hard stop.

#### Scenario: Production allowed after fresh dark-control validation

- GIVEN a validated dark-control record exists for `new-camera-mount`
- WHEN an operator starts a production statistical run
- THEN the gate check passes
- AND the run is authorized for production registration

#### Scenario: Production blocked when dark-control is missing

- GIVEN no validated dark-control record exists for `new-camera-mount`
- WHEN an operator starts a production statistical run
- THEN the gate check fails
- AND production registration is blocked with a corrective action message

### Requirement: Dark-Control Traceability

Production run metadata SHALL include a reference to the validating dark-control record used to satisfy the gate.

#### Scenario: Run metadata contains dark-control reference

- GIVEN production run authorization succeeds
- WHEN run metadata is finalized
- THEN metadata includes a dark-control reference identifier
- AND the reference resolves to a `new-camera-mount` dark-control record

#### Scenario: Mismatched mount dark-control is rejected

- GIVEN a dark-control record from a legacy mount context
- WHEN it is provided for `new-camera-mount` gate satisfaction
- THEN validation fails
- AND production run authorization is denied
