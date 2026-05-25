from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .io import (
    read_csv_header_and_count,
    read_csv_rows,
    read_json,
    read_key_value_csv,
    relative_path,
    string_value,
    write_csv,
)
from .models import RunRecord, RunSummary, ValidationRecord
from .validate import (
    STATUS_LEGACY,
    STATUS_MISSING,
    STATUS_VALID,
    aggregate_run_status,
    validate_csv_artifact,
    validate_path_artifact,
)


WEBCAM_COLUMNS = ["timestamp_s", "frame_index", "mean", "max", "p99", "threshold", "detected"]
DUAL_WEBCAM_COLUMNS = [
    "timestamp_s",
    "perf_counter_s",
    "frame_index",
    "mean",
    "max",
    "p99",
    "threshold",
    "detected",
]
KV_COLUMNS = ["field", "value"]
OP598_COLUMNS = ["index", "t_us", "t_ms", "adc", "led", "phase", "pulse_index"]
DUAL_PULSE_COLUMNS = [
    "pulse_index",
    "start_ms",
    "end_ms",
    "duration_ms",
    "anchor_ms",
    "peak_ms",
    "peak_adc",
    "mean_adc",
    "baseline_adc",
    "threshold_adc",
    "sample_count",
    "op598_detected",
]
DUAL_COINCIDENCE_COLUMNS = [
    "pulse_index",
    "op598_anchor_ms",
    "nearest_frame_index",
    "matched_frame_index",
    "detected_in_window",
    "matched_frame_detected",
]
LATENCY_RESULTS_COLUMNS = ["trial", "latency_us", "adc"]
LATENCY_SUMMARY_COLUMNS = [
    "min_latency_us",
    "max_latency_us",
    "avg_latency_us",
    "median_latency_us",
    "failures",
]
TIMESTAMP_PATTERN = re.compile(r"(?P<ts>\d{8}_\d{6}|\d{8})")


def infer_created_at(name: str) -> str:
    match = TIMESTAMP_PATTERN.search(name)
    return match.group("ts") if match else ""


def normalize_variant(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return "/".join(rel.parts[2:-1]) if len(rel.parts) > 3 else "."


def csv_sum(rows: list[dict[str, str]], key: str) -> int:
    total = 0
    for row in rows:
        value = row.get(key, "")
        if not value:
            continue
        total += int(float(value))
    return total


def first_present(mapping: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key, "")
        if value != "":
            return value
    return ""


def is_webcam_sweep_csv(path: Path) -> bool:
    header, row_count = read_csv_header_and_count(path)
    return row_count > 0 and "csv" in header and "detection_events" in header


def validate_webcam_sweep_links(root: Path, run_id: str, csv_path: Path) -> ValidationRecord:
    rows = read_csv_rows(csv_path)
    linked_paths = [root / row.get("csv", "") for row in rows if row.get("csv", "")]
    missing = [relative_path(path, root) for path in linked_paths if not path.exists()]
    status = STATUS_MISSING if missing else STATUS_VALID
    return ValidationRecord(
        run_id=run_id,
        family="webcam",
        artifact_kind="webcam_sweep_companion_csvs",
        artifact_path=relative_path(csv_path, root),
        required="true",
        status=status,
        exists="true",
        schema_ok=str(not missing).lower(),
        row_count=str(len(linked_paths)),
        missing_columns="",
        details="missing=" + ";".join(missing) if missing else "all companion csv paths exist",
    )


def validate_dual_webcam_metrics(root: Path, run_id: str, path: Path) -> ValidationRecord:
    if not path.exists():
        return validate_csv_artifact(
            root=root,
            run_id=run_id,
            family="dual_experiments",
            artifact_kind="webcam_metrics_csv",
            path=path,
            expected_columns=DUAL_WEBCAM_COLUMNS,
            required=True,
        )

    header, row_count = read_csv_header_and_count(path)
    if all(column in header for column in DUAL_WEBCAM_COLUMNS):
        return validate_csv_artifact(
            root=root,
            run_id=run_id,
            family="dual_experiments",
            artifact_kind="webcam_metrics_csv",
            path=path,
            expected_columns=DUAL_WEBCAM_COLUMNS,
            required=True,
        )
    if all(column in header for column in WEBCAM_COLUMNS):
        return ValidationRecord(
            run_id=run_id,
            family="dual_experiments",
            artifact_kind="webcam_metrics_csv",
            artifact_path=relative_path(path, root),
            required="true",
            status=STATUS_VALID,
            exists="true",
            schema_ok="true",
            row_count=str(row_count),
            missing_columns="",
            details="perf_counter_s inferred from timestamp_s;" + ",".join(header),
        )
    return validate_csv_artifact(
        root=root,
        run_id=run_id,
        family="dual_experiments",
        artifact_kind="webcam_metrics_csv",
        path=path,
        expected_columns=DUAL_WEBCAM_COLUMNS,
        required=True,
    )


def discover_webcam_runs(root: Path) -> tuple[list[RunRecord], list[ValidationRecord], list[RunSummary]]:
    runs: list[RunRecord] = []
    validations: list[ValidationRecord] = []
    summaries: list[RunSummary] = []
    family_root = root / "data" / "webcam"
    if not family_root.exists():
        return runs, validations, summaries

    for csv_path in sorted(family_root.glob("*.csv")):
        run_id = csv_path.stem
        structured = run_id.startswith("webcam_flash_metrics_")
        normalizable_sweep = not structured and is_webcam_sweep_csv(csv_path)
        run_validations: list[ValidationRecord] = []
        notes = ""
        if structured:
            run_validations.append(
                validate_csv_artifact(
                    root=root,
                    run_id=run_id,
                    family="webcam",
                    artifact_kind="webcam_metrics_csv",
                    path=csv_path,
                    expected_columns=WEBCAM_COLUMNS,
                    required=True,
                )
            )
            rows = read_csv_rows(csv_path)
            summary = RunSummary(
                run_id=run_id,
                family="webcam",
                variant=".",
                status=aggregate_run_status(run_validations),
                mode="flash-metrics",
                created_at=infer_created_at(run_id),
                webcam_frames=str(len(rows)),
                webcam_detected_frames=str(csv_sum(rows, "detected")),
                notes="CSV de métricas de flashes por webcam",
            )
        elif normalizable_sweep:
            notes = "Sweep webcam heredado normalizado por enlaces a CSVs de metricas"
            run_validations.append(
                validate_path_artifact(
                    root=root,
                    run_id=run_id,
                    family="webcam",
                    artifact_kind="legacy_sweep_csv",
                    path=csv_path,
                    required=True,
                )
            )
            run_validations.append(validate_webcam_sweep_links(root, run_id, csv_path))
            rows = read_csv_rows(csv_path)
            summary = RunSummary(
                run_id=run_id,
                family="webcam",
                variant=".",
                status=aggregate_run_status(run_validations),
                mode="legacy-sweep",
                created_at=infer_created_at(run_id),
                webcam_detection_events=str(csv_sum(rows, "detection_events")),
                webcam_detected_frames=str(csv_sum(rows, "detected_frames")),
                notes=notes,
            )
        else:
            notes = "CSV heredado fuera del formato de métricas de webcam"
            run_validations.append(
                validate_path_artifact(
                    root=root,
                    run_id=run_id,
                    family="webcam",
                    artifact_kind="legacy_csv",
                    path=csv_path,
                    required=True,
                )
            )
            summary = RunSummary(
                run_id=run_id,
                family="webcam",
                variant=".",
                status=STATUS_LEGACY,
                mode="legacy-csv",
                created_at=infer_created_at(run_id),
                notes=notes,
            )

        status = aggregate_run_status(run_validations, legacy=not structured and not normalizable_sweep)
        runs.append(
            RunRecord(
                run_id=run_id,
                family="webcam",
                variant=".",
                source_path=relative_path(csv_path, root),
                status=status,
                kind="artifact_group" if normalizable_sweep else "standalone_csv",
                created_at=infer_created_at(run_id),
                mode=summary.mode,
                primary_artifact=relative_path(csv_path, root),
                notes=notes,
            )
        )
        summary.status = status
        validations.extend(run_validations)
        summaries.append(summary)
    return runs, validations, summaries


def group_op598_artifacts(family_root: Path) -> dict[str, set[Path]]:
    groups: dict[str, set[Path]] = {}
    for path in sorted(family_root.rglob("*")):
        if not path.is_file():
            continue
        if not path.name.startswith("op598_"):
            continue
        if path.suffix == ".md" and not path.name.endswith("_summary.md"):
            continue
        stem = path.stem
        if stem.endswith("_summary"):
            stem = stem[: -len("_summary")]
        groups.setdefault(stem, set()).add(path)
    return groups


def discover_op598_runs(root: Path) -> tuple[list[RunRecord], list[ValidationRecord], list[RunSummary]]:
    runs: list[RunRecord] = []
    validations: list[ValidationRecord] = []
    summaries: list[RunSummary] = []
    family_root = root / "data" / "op598"
    if not family_root.exists():
        return runs, validations, summaries

    for run_id, files in sorted(group_op598_artifacts(family_root).items()):
        parent = sorted(files)[0].parent
        variant = str(parent.relative_to(family_root)) if parent != family_root else "."
        raw_csv = next((path for path in files if path.suffix == ".csv" and not path.stem.endswith("_summary")), None)
        summary_csv = next((path for path in files if path.name.endswith("_summary.csv")), None)
        summary_md = next((path for path in files if path.name.endswith("_summary.md")), None)
        plot_png = next((path for path in files if path.suffix == ".png"), None)
        log_path = next((path for path in files if path.suffix == ".log"), None)

        structured = raw_csv is not None or summary_csv is not None
        run_validations: list[ValidationRecord] = []
        notes = ""
        metadata: dict[str, str] = {}
        if structured:
            run_validations.append(
                validate_csv_artifact(
                    root=root,
                    run_id=run_id,
                    family="op598",
                    artifact_kind="op598_raw_csv",
                    path=raw_csv or (family_root / f"{run_id}.csv"),
                    expected_columns=OP598_COLUMNS,
                    required=True,
                )
            )
            run_validations.append(
                validate_csv_artifact(
                    root=root,
                    run_id=run_id,
                    family="op598",
                    artifact_kind="op598_summary_csv",
                    path=summary_csv or (family_root / f"{run_id}_summary.csv"),
                    expected_columns=KV_COLUMNS,
                    required=True,
                )
            )
            if summary_md is not None:
                run_validations.append(
                    validate_path_artifact(
                        root=root,
                        run_id=run_id,
                        family="op598",
                        artifact_kind="op598_summary_md",
                        path=summary_md,
                        required=False,
                    )
                )
            if plot_png is not None:
                run_validations.append(
                    validate_path_artifact(
                        root=root,
                        run_id=run_id,
                        family="op598",
                        artifact_kind="op598_plot_png",
                        path=plot_png,
                        required=False,
                    )
                )
            if log_path is not None:
                run_validations.append(
                    validate_path_artifact(
                        root=root,
                        run_id=run_id,
                        family="op598",
                        artifact_kind="op598_log",
                        path=log_path,
                        required=False,
                    )
                )
            if summary_csv is not None and summary_csv.exists():
                metadata = read_key_value_csv(summary_csv)
            notes = "Captura OP598 con artefactos agrupados por prefijo temporal"
        else:
            notes = "Artefacto OP598 sin pareja tabular reproducible"
            for file_path in sorted(files):
                run_validations.append(
                    validate_path_artifact(
                        root=root,
                        run_id=run_id,
                        family="op598",
                        artifact_kind=file_path.suffix.lstrip(".") or "artifact",
                        path=file_path,
                        required=True,
                    )
                )

        status = aggregate_run_status(run_validations, legacy=not structured)
        runs.append(
            RunRecord(
                run_id=run_id,
                family="op598",
                variant=variant,
                source_path=relative_path(parent, root),
                status=status,
                kind="artifact_group",
                created_at=infer_created_at(run_id),
                mode=run_id.removeprefix("op598_").rsplit("_", 1)[0],
                primary_artifact=relative_path(raw_csv or sorted(files)[0], root),
                notes=notes,
            )
        )
        summaries.append(
            RunSummary(
                run_id=run_id,
                family="op598",
                variant=variant,
                status=status,
                mode=first_present(metadata, "command") or run_id.removeprefix("op598_").rsplit("_", 1)[0],
                created_at=infer_created_at(run_id),
                pulse_count=first_present(metadata, "pulse_count"),
                op598_sample_count=first_present(metadata, "sample_count"),
                op598_peak_adc=first_present(metadata, "peak_adc"),
                notes=notes,
            )
        )
        validations.extend(run_validations)

    for md_path in sorted(family_root.glob("*.md")):
        if md_path.name.startswith("op598_") and md_path.name.endswith("_summary.md"):
            continue
        run_id = md_path.stem
        validation = validate_path_artifact(
            root=root,
            run_id=run_id,
            family="op598",
            artifact_kind="legacy_md",
            path=md_path,
            required=True,
        )
        runs.append(
            RunRecord(
                run_id=run_id,
                family="op598",
                variant=".",
                source_path=relative_path(md_path, root),
                status=STATUS_LEGACY,
                kind="standalone_doc",
                created_at=infer_created_at(run_id),
                primary_artifact=relative_path(md_path, root),
                notes="Documento descriptivo no emparejado con una corrida única",
            )
        )
        summaries.append(
            RunSummary(
                run_id=run_id,
                family="op598",
                variant=".",
                status=STATUS_LEGACY,
                created_at=infer_created_at(run_id),
                notes="Documento heredado fuera del modelo tabular",
            )
        )
        validations.append(validation)
    return runs, validations, summaries


def dual_run_directories(family_root: Path) -> list[Path]:
    candidates: set[Path] = set()
    for path in family_root.rglob("manifest.json"):
        candidates.add(path.parent)
    for path in family_root.rglob("dual_summary.csv"):
        candidates.add(path.parent)
    return sorted(candidates)


def discover_dual_runs(root: Path) -> tuple[list[RunRecord], list[ValidationRecord], list[RunSummary]]:
    runs: list[RunRecord] = []
    validations: list[ValidationRecord] = []
    summaries: list[RunSummary] = []
    family_root = root / "data" / "dual_experiments"
    if not family_root.exists():
        return runs, validations, summaries

    for run_dir in dual_run_directories(family_root):
        run_id = run_dir.name
        variant = str(run_dir.relative_to(family_root).parent)
        manifest_path = run_dir / "manifest.json"
        manifest = read_json(manifest_path) if manifest_path.exists() else {}
        artifacts = manifest.get("artifacts", {}) if isinstance(manifest.get("artifacts", {}), dict) else {}

        def artifact_path(key: str, default: Path) -> Path:
            value = artifacts.get(key)
            if isinstance(value, str) and value:
                return root / value
            return default

        webcam_csv = artifact_path("webcam_csv", run_dir / "webcam_metrics.csv")
        pulse_csv = artifact_path("pulse_events_csv", run_dir / "pulse_events.csv")
        coincidence_csv = artifact_path("coincidence_csv", run_dir / "coincidence_table.csv")
        summary_csv = artifact_path("summary_csv", run_dir / "dual_summary.csv")
        summary_md = artifact_path("summary_md", run_dir / "dual_summary.md")
        webcam_frames_dir = artifact_path("webcam_frames", run_dir / "webcam_frames")
        op598_dir = artifact_path("op598_dir", run_dir / "op598")

        run_validations = [
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="dual_summary_csv",
                path=summary_csv,
                expected_columns=KV_COLUMNS,
                required=True,
            ),
            validate_dual_webcam_metrics(root, run_id, webcam_csv),
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="pulse_events_csv",
                path=pulse_csv,
                expected_columns=DUAL_PULSE_COLUMNS,
                required=True,
            ),
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="coincidence_table_csv",
                path=coincidence_csv,
                expected_columns=DUAL_COINCIDENCE_COLUMNS,
                required=True,
            ),
            validate_path_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="dual_summary_md",
                path=summary_md,
                required=False,
            ),
            validate_path_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="webcam_frames_dir",
                path=webcam_frames_dir,
                required=False,
            ),
            validate_path_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="op598_dir",
                path=op598_dir,
                required=True,
            ),
        ]

        op598_files = sorted(op598_dir.glob("*.csv")) if op598_dir.exists() else []
        op598_raw = next((path for path in op598_files if not path.stem.endswith("_summary")), None)
        op598_summary = next((path for path in op598_files if path.stem.endswith("_summary")), None)
        run_validations.append(
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="op598_raw_csv",
                path=op598_raw or (op598_dir / "missing.csv"),
                expected_columns=OP598_COLUMNS,
                required=True,
            )
        )
        run_validations.append(
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="dual_experiments",
                artifact_kind="op598_summary_csv",
                path=op598_summary or (op598_dir / "missing_summary.csv"),
                expected_columns=KV_COLUMNS,
                required=True,
            )
        )

        summary_values = read_key_value_csv(summary_csv) if summary_csv.exists() else {}
        if not summary_values and isinstance(manifest.get("op598_summary"), dict):
            summary_values = {str(key): string_value(value) for key, value in manifest["op598_summary"].items()}
        if summary_csv.exists() and webcam_csv.exists():
            webcam_rows = read_csv_rows(webcam_csv)
        else:
            webcam_rows = []

        status = aggregate_run_status(run_validations)
        runs.append(
            RunRecord(
                run_id=run_id,
                family="dual_experiments",
                variant=variant,
                source_path=relative_path(run_dir, root),
                status=status,
                kind="run_directory",
                created_at=string_value(manifest.get("created_at", "")) or infer_created_at(run_id),
                mode=string_value(manifest.get("mode", "")) or first_present(summary_values, "mode"),
                primary_artifact=relative_path(summary_csv, root),
                manifest_path=relative_path(manifest_path, root) if manifest_path.exists() else "",
                notes="Corrida dual correlacionando webcam y OP598",
            )
        )
        summaries.append(
            RunSummary(
                run_id=run_id,
                family="dual_experiments",
                variant=variant,
                status=status,
                mode=string_value(manifest.get("mode", "")) or first_present(summary_values, "mode"),
                created_at=string_value(manifest.get("created_at", "")) or infer_created_at(run_id),
                pulse_count=first_present(summary_values, "op598.pulse_count", "op598.pulse_events", "pulse_count"),
                webcam_frames=first_present(summary_values, "webcam.frames") or string_value(len(webcam_rows)),
                webcam_detected_frames=first_present(summary_values, "webcam.detected_frames") or string_value(csv_sum(webcam_rows, "detected")),
                webcam_detection_events=first_present(summary_values, "webcam.detection_events"),
                op598_sample_count=first_present(summary_values, "op598.sample_count", "sample_count"),
                op598_peak_adc=first_present(summary_values, "op598.peak_adc", "peak_adc"),
                notes="Resumen normalizado desde dual_summary.csv y manifest.json",
            )
        )
        validations.extend(run_validations)
    return runs, validations, summaries


def discover_latency_runs(root: Path) -> tuple[list[RunRecord], list[ValidationRecord], list[RunSummary]]:
    runs: list[RunRecord] = []
    validations: list[ValidationRecord] = []
    summaries: list[RunSummary] = []
    family_root = root / "data" / "latency_runs"
    if not family_root.exists():
        return runs, validations, summaries

    results_files = sorted(family_root.glob("*_results_*.csv"))
    for results_csv in results_files:
        run_id = results_csv.stem
        timestamp = infer_created_at(run_id)
        summary_stem = results_csv.name.replace("_results_", "_summary_")
        summary_csv = family_root / summary_stem
        log_name = results_csv.name.replace("_results_", "_log_").replace(".csv", ".txt")
        log_path = family_root / log_name
        run_validations = [
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="latency_runs",
                artifact_kind="latency_results_csv",
                path=results_csv,
                expected_columns=LATENCY_RESULTS_COLUMNS,
                required=True,
            ),
            validate_csv_artifact(
                root=root,
                run_id=run_id,
                family="latency_runs",
                artifact_kind="latency_summary_csv",
                path=summary_csv,
                expected_columns=LATENCY_SUMMARY_COLUMNS,
                required=True,
            ),
            validate_path_artifact(
                root=root,
                run_id=run_id,
                family="latency_runs",
                artifact_kind="latency_log_txt",
                path=log_path,
                required=False,
            ),
        ]
        summary_rows = read_csv_rows(summary_csv) if summary_csv.exists() else []
        summary_row = summary_rows[0] if summary_rows else {}
        status = aggregate_run_status(run_validations)
        runs.append(
            RunRecord(
                run_id=run_id,
                family="latency_runs",
                variant=".",
                source_path=relative_path(results_csv, root),
                status=status,
                kind="artifact_group",
                created_at=timestamp,
                mode="latency",
                primary_artifact=relative_path(results_csv, root),
                notes="Corrida opcional de latencia agrupada por timestamp",
            )
        )
        summaries.append(
            RunSummary(
                run_id=run_id,
                family="latency_runs",
                variant=".",
                status=status,
                mode="latency",
                created_at=timestamp,
                latency_avg_us=string_value(summary_row.get("avg_latency_us", "")),
                latency_failures=string_value(summary_row.get("failures", "")),
                notes="Resumen opcional de latencia",
            )
        )
        validations.extend(run_validations)
    return runs, validations, summaries


def build_catalog_outputs(repo_root: Path, output_dir: Path, include_latency: bool = True) -> dict[str, object]:
    scanners = [discover_webcam_runs, discover_op598_runs, discover_dual_runs]
    if include_latency:
        scanners.append(discover_latency_runs)

    run_records: list[RunRecord] = []
    validation_records: list[ValidationRecord] = []
    summary_records: list[RunSummary] = []
    for scanner in scanners:
        runs, validations, summaries = scanner(repo_root)
        run_records.extend(runs)
        validation_records.extend(validations)
        summary_records.extend(summaries)

    run_rows = [record.to_row() for record in sorted(run_records, key=lambda item: (item.family, item.variant, item.run_id))]
    validation_rows = [record.to_row() for record in sorted(validation_records, key=lambda item: (item.family, item.run_id, item.artifact_kind, item.artifact_path))]
    summary_rows = [record.to_row() for record in sorted(summary_records, key=lambda item: (item.family, item.variant, item.run_id))]

    runs_catalog = output_dir / "runs_catalog.csv"
    validation_report = output_dir / "validation_report.csv"
    run_summaries = output_dir / "run_summaries.csv"
    write_csv(runs_catalog, run_rows)
    write_csv(validation_report, validation_rows)
    write_csv(run_summaries, summary_rows)

    family_counts = Counter(record.family for record in run_records)
    status_counts = Counter(record.status for record in run_records)
    family_status_counts = Counter((record.family, record.status) for record in run_records)
    return {
        "runs_catalog": runs_catalog,
        "validation_report": validation_report,
        "run_summaries": run_summaries,
        "run_count": len(run_records),
        "validation_count": len(validation_records),
        "summary_count": len(summary_records),
        "family_counts": dict(sorted(family_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "family_status_counts": {
            f"{family}:{status}": count
            for (family, status), count in sorted(family_status_counts.items())
        },
    }
