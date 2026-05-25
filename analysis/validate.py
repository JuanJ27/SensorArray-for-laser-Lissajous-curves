from __future__ import annotations

from pathlib import Path

from .io import read_csv_header_and_count, relative_path
from .models import ValidationRecord


STATUS_VALID = "valid"
STATUS_PARTIAL = "partial"
STATUS_MISSING = "missing_artifact"
STATUS_SCHEMA = "schema_mismatch"
STATUS_LEGACY = "legacy_unstructured"
STATUS_EMPTY = "invalid_empty"


def validate_csv_artifact(
    *,
    root: Path,
    run_id: str,
    family: str,
    artifact_kind: str,
    path: Path,
    expected_columns: list[str],
    required: bool,
) -> ValidationRecord:
    if not path.exists():
        return ValidationRecord(
            run_id=run_id,
            family=family,
            artifact_kind=artifact_kind,
            artifact_path=relative_path(path, root),
            required=str(required).lower(),
            status=STATUS_MISSING,
            exists="false",
            schema_ok="false",
            row_count="",
            details="file not found",
        )

    header, row_count = read_csv_header_and_count(path)
    if not header and row_count == 0:
        return ValidationRecord(
            run_id=run_id,
            family=family,
            artifact_kind=artifact_kind,
            artifact_path=relative_path(path, root),
            required=str(required).lower(),
            status=STATUS_EMPTY,
            exists="true",
            schema_ok="false",
            row_count="0",
            missing_columns=",".join(expected_columns),
            details="empty csv",
        )
    missing_columns = [column for column in expected_columns if column not in header]
    status = STATUS_VALID if not missing_columns else STATUS_SCHEMA
    return ValidationRecord(
        run_id=run_id,
        family=family,
        artifact_kind=artifact_kind,
        artifact_path=relative_path(path, root),
        required=str(required).lower(),
        status=status,
        exists="true",
        schema_ok=str(not missing_columns).lower(),
        row_count=str(row_count),
        missing_columns=",".join(missing_columns),
        details=",".join(header),
    )


def validate_path_artifact(
    *,
    root: Path,
    run_id: str,
    family: str,
    artifact_kind: str,
    path: Path,
    required: bool,
) -> ValidationRecord:
    exists = path.exists()
    status = STATUS_VALID if exists else STATUS_MISSING
    details = "directory present" if path.is_dir() else "file present"
    if not exists:
        details = "path not found"
    return ValidationRecord(
        run_id=run_id,
        family=family,
        artifact_kind=artifact_kind,
        artifact_path=relative_path(path, root),
        required=str(required).lower(),
        status=status,
        exists=str(exists).lower(),
        schema_ok=str(exists).lower(),
        row_count="",
        details=details,
    )


def aggregate_run_status(records: list[ValidationRecord], legacy: bool = False) -> str:
    if legacy:
        return STATUS_LEGACY
    required_records = [record for record in records if record.required == "true"]
    if any(record.status == STATUS_EMPTY for record in required_records):
        return STATUS_EMPTY
    if any(record.status == STATUS_SCHEMA for record in required_records):
        return STATUS_SCHEMA
    if any(record.status == STATUS_MISSING for record in required_records):
        return STATUS_PARTIAL
    return STATUS_VALID
