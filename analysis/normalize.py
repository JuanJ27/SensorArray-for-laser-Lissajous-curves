from __future__ import annotations

from collections import Counter
from pathlib import Path

from .catalog import (
    DUAL_WEBCAM_COLUMNS,
    WEBCAM_COLUMNS,
    build_catalog_outputs,
    dual_run_directories,
    infer_created_at,
    is_webcam_sweep_csv,
    validate_webcam_sweep_links,
)
from .io import read_csv_header_and_count, read_csv_rows, relative_path, write_csv
from .validate import STATUS_EMPTY, STATUS_LEGACY, STATUS_PARTIAL, STATUS_VALID


def row_count(path: Path) -> int:
    if not path.exists():
        return 0
    _, count = read_csv_header_and_count(path)
    return count


def normalize_dual_runs(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    report: list[dict[str, object]] = []
    family_root = root / "data" / "dual_experiments"
    if not family_root.exists():
        return rows, report

    for run_dir in dual_run_directories(family_root):
        run_id = run_dir.name
        webcam_csv = run_dir / "webcam_metrics.csv"
        pulse_csv = run_dir / "pulse_events.csv"
        coincidence_csv = run_dir / "coincidence_table.csv"
        header, webcam_count = read_csv_header_and_count(webcam_csv) if webcam_csv.exists() else ([], 0)
        can_infer_perf_counter = "perf_counter_s" not in header and all(column in header for column in WEBCAM_COLUMNS)
        has_current_schema = all(column in header for column in DUAL_WEBCAM_COLUMNS)
        missing_core = [path.name for path in [run_dir / "dual_summary.csv", webcam_csv, run_dir / "op598"] if not path.exists()]
        missing_reconstructable = [path.name for path in [pulse_csv, coincidence_csv] if not path.exists()]
        if missing_core:
            normalized_status = STATUS_LEGACY
            policy = "unrecoverable_missing_core"
        elif has_current_schema and not missing_reconstructable:
            normalized_status = STATUS_VALID
            policy = "current_schema"
        elif has_current_schema or can_infer_perf_counter:
            normalized_status = STATUS_PARTIAL if missing_reconstructable else STATUS_VALID
            policy = "perf_counter_s_inferred_from_timestamp" if can_infer_perf_counter else "partial_missing_derived_tables"
        else:
            normalized_status = STATUS_LEGACY
            policy = "unrecoverable_webcam_schema"
        rows.append(
            {
                "run_id": run_id,
                "family": "dual_experiments",
                "variant": str(run_dir.relative_to(family_root).parent),
                "source_path": relative_path(run_dir, root),
                "normalized_status": normalized_status,
                "normalization_policy": policy,
                "primary_artifact": relative_path(webcam_csv, root),
                "created_at": infer_created_at(run_id),
                "webcam_rows": webcam_count,
                "perf_counter_s_inferred_from_timestamp": str(can_infer_perf_counter).lower(),
                "linked_artifacts": ";".join(relative_path(path, root) for path in [pulse_csv, coincidence_csv] if path.exists()),
                "unrecoverable_reason": ";".join(missing_core + missing_reconstructable),
            }
        )
        if can_infer_perf_counter or missing_reconstructable or missing_core:
            report.append(
                {
                    "run_id": run_id,
                    "family": "dual_experiments",
                    "artifact_path": relative_path(run_dir, root),
                    "action": policy,
                    "status": normalized_status,
                    "details": "missing=" + ";".join(missing_core + missing_reconstructable),
                }
            )
    return rows, report


def normalize_webcam_legacy(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    report: list[dict[str, object]] = []
    family_root = root / "data" / "webcam"
    if not family_root.exists():
        return rows, report

    for csv_path in sorted(family_root.glob("*.csv")):
        if csv_path.name.startswith("webcam_flash_metrics_") or not is_webcam_sweep_csv(csv_path):
            continue
        run_id = csv_path.stem
        link_validation = validate_webcam_sweep_links(root, run_id, csv_path)
        rows_data = read_csv_rows(csv_path)
        normalized_status = STATUS_VALID if link_validation.status == STATUS_VALID else STATUS_PARTIAL
        rows.append(
            {
                "run_id": run_id,
                "family": "webcam",
                "variant": ".",
                "source_path": relative_path(csv_path, root),
                "normalized_status": normalized_status,
                "normalization_policy": "legacy_sweep_companion_csv_links",
                "primary_artifact": relative_path(csv_path, root),
                "created_at": infer_created_at(run_id),
                "webcam_rows": len(rows_data),
                "perf_counter_s_inferred_from_timestamp": "false",
                "linked_artifacts": ";".join(row.get("csv", "") for row in rows_data if row.get("csv", "")),
                "unrecoverable_reason": "" if normalized_status == STATUS_VALID else link_validation.details,
            }
        )
        report.append(
            {
                "run_id": run_id,
                "family": "webcam",
                "artifact_path": relative_path(csv_path, root),
                "action": "grouped legacy sweep with companion metric CSVs",
                "status": normalized_status,
                "details": link_validation.details,
            }
        )
    return rows, report


def normalize_latency_empty(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    report: list[dict[str, object]] = []
    family_root = root / "data" / "latency_runs"
    if not family_root.exists():
        return rows, report

    for results_csv in sorted(family_root.glob("*_results_*.csv")):
        header, count = read_csv_header_and_count(results_csv)
        if header or count:
            continue
        run_id = results_csv.stem
        summary_csv = family_root / results_csv.name.replace("_results_", "_summary_")
        log_path = family_root / results_csv.name.replace("_results_", "_log_").replace(".csv", ".txt")
        linked = [path for path in [summary_csv, log_path] if path.exists()]
        rows.append(
            {
                "run_id": run_id,
                "family": "latency_runs",
                "variant": ".",
                "source_path": relative_path(results_csv, root),
                "normalized_status": STATUS_EMPTY,
                "normalization_policy": "empty_latency_csv_preserve_companions",
                "primary_artifact": relative_path(results_csv, root),
                "created_at": infer_created_at(run_id),
                "webcam_rows": "",
                "perf_counter_s_inferred_from_timestamp": "false",
                "linked_artifacts": ";".join(relative_path(path, root) for path in linked),
                "unrecoverable_reason": "latency results csv is empty",
            }
        )
        report.append(
            {
                "run_id": run_id,
                "family": "latency_runs",
                "artifact_path": relative_path(results_csv, root),
                "action": "marked invalid empty without fabrication",
                "status": STATUS_EMPTY,
                "details": "linked=" + ";".join(relative_path(path, root) for path in linked),
            }
        )
    return rows, report


def mark_unrecoverable_loose_artifacts(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    report: list[dict[str, object]] = []
    candidates: list[tuple[str, Path, str]] = []
    op598_root = root / "data" / "op598"
    webcam_root = root / "data" / "webcam"
    if op598_root.exists():
        for path in sorted(op598_root.glob("*.log")):
            if not (op598_root / f"{path.stem}.csv").exists():
                candidates.append(("op598", path, "loose log without raw csv"))
        for path in sorted(op598_root.glob("*.md")):
            if not path.name.endswith("_summary.md"):
                candidates.append(("op598", path, "standalone documentation, not a run table"))
    if webcam_root.exists():
        for path in sorted(webcam_root.glob("*.md")):
            candidates.append(("webcam", path, "standalone documentation, not a run table"))

    for family, path, reason in candidates:
        run_id = path.stem
        rows.append(
            {
                "run_id": run_id,
                "family": family,
                "variant": ".",
                "source_path": relative_path(path, root),
                "normalized_status": STATUS_LEGACY,
                "normalization_policy": "unrecoverable_loose_artifact",
                "primary_artifact": relative_path(path, root),
                "created_at": infer_created_at(run_id),
                "webcam_rows": "",
                "perf_counter_s_inferred_from_timestamp": "false",
                "linked_artifacts": "",
                "unrecoverable_reason": reason,
            }
        )
        report.append(
            {
                "run_id": run_id,
                "family": family,
                "artifact_path": relative_path(path, root),
                "action": "marked unrecoverable loose artifact",
                "status": STATUS_LEGACY,
                "details": reason,
            }
        )
    return rows, report


def build_normalization_outputs(repo_root: Path, output_dir: Path) -> dict[str, object]:
    normalized_rows: list[dict[str, object]] = []
    report_rows: list[dict[str, object]] = []
    for normalizer in [
        normalize_dual_runs,
        normalize_webcam_legacy,
        normalize_latency_empty,
        mark_unrecoverable_loose_artifacts,
    ]:
        rows, report = normalizer(repo_root)
        normalized_rows.extend(rows)
        report_rows.extend(report)

    normalized_runs = output_dir / "normalized_runs.csv"
    normalization_report = output_dir / "normalization_report.csv"
    write_csv(normalized_runs, sorted(normalized_rows, key=lambda row: (str(row["family"]), str(row["run_id"]))))
    write_csv(normalization_report, sorted(report_rows, key=lambda row: (str(row["family"]), str(row["run_id"]), str(row["action"]))))

    catalog_output_dir = repo_root / "data" / "derived" / "catalog"
    catalog_results = build_catalog_outputs(repo_root, catalog_output_dir)
    status_counts = Counter(str(row["normalized_status"]) for row in normalized_rows)
    return {
        "normalized_runs": normalized_runs,
        "normalization_report": normalization_report,
        "normalized_run_count": len(normalized_rows),
        "normalization_report_count": len(report_rows),
        "normalized_status_counts": dict(sorted(status_counts.items())),
        "catalog_status_counts_after_policy": catalog_results["status_counts"],
    }
