from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class RunRecord:
    run_id: str
    family: str
    variant: str
    source_path: str
    status: str
    kind: str
    created_at: str = ""
    mode: str = ""
    primary_artifact: str = ""
    manifest_path: str = ""
    notes: str = ""

    def to_row(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ValidationRecord:
    run_id: str
    family: str
    artifact_kind: str
    artifact_path: str
    required: str
    status: str
    exists: str
    schema_ok: str
    row_count: str
    missing_columns: str = ""
    details: str = ""

    def to_row(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RunSummary:
    run_id: str
    family: str
    variant: str
    status: str
    mode: str = ""
    created_at: str = ""
    pulse_count: str = ""
    webcam_frames: str = ""
    webcam_detected_frames: str = ""
    webcam_detection_events: str = ""
    op598_sample_count: str = ""
    op598_peak_adc: str = ""
    latency_avg_us: str = ""
    latency_failures: str = ""
    notes: str = ""

    def to_row(self) -> dict[str, object]:
        return asdict(self)
