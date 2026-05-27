from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from .io import ensure_directory, read_csv_rows, read_key_value_csv, write_csv
from .presentation import build_presentation_plots
from .uncertainty import bootstrap_threshold_estimates, estimate_detection_thresholds, wilson_interval


ACK_COUNT_PATTERN = re.compile(r"count=(?P<count>\d+)")
DUAL_RUN_PATTERN = re.compile(r"random-train_\d{8}_\d{6}")

CAMERA0_THRESHOLD_CAMPAIGN_ID = "camera0-intensity-threshold-statistics"
REQUIRED_CAMERA0_DUTIES = {
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    10,
    12,
    16,
    24,
    32,
    48,
    64,
    128,
}
REQUIRED_CAMERA0_POSITIVE_CONTROLS = {16, 24, 32, 48, 64, 128}
FIXED_PULSES_PER_DUTY = 60
MIN_PULSES_PER_DUTY = 30
REQUIRED_CAMERA0_PER_PULSE_COLUMNS = (
    "campaign_id",
    "run_id",
    "camera_index",
    "duty",
    "pulse_index",
    "detected_any",
    "detected_frames",
    "detection_events",
    "expected_pulses",
    "block_id",
    "block_order",
    "is_dark_control",
    "is_positive_control",
    "acquisition_fingerprint",
)
REQUIRED_CAMERA0_PLAN_COLUMNS = (
    "campaign_id",
    "camera_index",
    "duty",
    "pulse_index",
    "block_id",
    "block_order",
    "is_dark_control",
    "is_positive_control",
)

REQUIRED_CAMERA0_WILSON_COLUMNS = (
    "campaign_id",
    "camera_index",
    "duty",
    "n",
    "detected",
    "detection_rate",
    "wilson_low_95",
    "wilson_high_95",
)

REQUIRED_CAMERA0_THRESHOLD_COLUMNS = (
    "campaign_id",
    "camera_index",
    "duty50",
    "duty90",
    "duty95",
    "duty50_ci_low",
    "duty50_ci_high",
    "duty90_ci_low",
    "duty90_ci_high",
    "duty95_ci_low",
    "duty95_ci_high",
)

REQUIRED_CAMERA0_VALIDATION_COLUMNS = (
    "campaign_id",
    "camera_index",
    "is_compliant",
    "missing_duties",
    "under_replicated_duties",
    "below_fixed_target_duties",
    "excluded_rows",
    "accepted_rows",
    "resumen_es",
)


def _normalize_int(value: object | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate_camera0_plan_rows(plan_rows: list[dict[str, object]]) -> dict[str, object]:
    duty_counts: defaultdict[int, int] = defaultdict(int)
    block_duties: defaultdict[object, set[int]] = defaultdict(set)
    missing_columns = sorted(
        {
            column
            for row in plan_rows
            for column in REQUIRED_CAMERA0_PLAN_COLUMNS
            if column not in row
        }
    )
    for row in plan_rows:
        duty = _normalize_int(row.get("duty"))
        block_id = row.get("block_id")
        if duty is None:
            continue
        duty_counts[duty] += 1
        block_duties[block_id].add(duty)

    missing_duties = sorted(REQUIRED_CAMERA0_DUTIES.difference(duty_counts.keys()))
    under_replicated_duties = sorted(
        duty
        for duty in REQUIRED_CAMERA0_DUTIES
        if duty_counts.get(duty, 0) < MIN_PULSES_PER_DUTY
    )
    below_fixed_target = sorted(
        duty
        for duty in REQUIRED_CAMERA0_DUTIES
        if duty_counts.get(duty, 0) < FIXED_PULSES_PER_DUTY
    )
    expected_block_cardinality = len(REQUIRED_CAMERA0_DUTIES)
    has_interleaved_blocks = bool(
        block_duties
        and all(len(duties) == expected_block_cardinality for duties in block_duties.values())
    )
    return {
        "is_compliant": not missing_duties and not under_replicated_duties and has_interleaved_blocks and not missing_columns,
        "missing_duties": missing_duties,
        "under_replicated_duties": under_replicated_duties,
        "below_fixed_target_duties": below_fixed_target,
        "pulses_per_duty_target": FIXED_PULSES_PER_DUTY,
        "minimum_pulses_per_duty": MIN_PULSES_PER_DUTY,
        "has_interleaved_blocks": has_interleaved_blocks,
        "required_plan_columns": list(REQUIRED_CAMERA0_PLAN_COLUMNS),
        "missing_columns": missing_columns,
    }


def filter_camera0_campaign_rows(
    rows: list[dict[str, object]],
    campaign_id: str = CAMERA0_THRESHOLD_CAMPAIGN_ID,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    accepted: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []

    # Use modal fingerprint among rows with complete campaign+camera metadata.
    comparable_fingerprints = [
        str(row.get("acquisition_fingerprint", ""))
        for row in rows
        if row.get("campaign_id") == campaign_id and _normalize_int(row.get("camera_index")) == 0 and row.get("acquisition_fingerprint") not in (None, "")
    ]
    canonical_fingerprint = ""
    if comparable_fingerprints:
        canonical_fingerprint = max(set(comparable_fingerprints), key=comparable_fingerprints.count)

    for row in rows:
        campaign = row.get("campaign_id")
        camera_index = _normalize_int(row.get("camera_index"))
        fingerprint = row.get("acquisition_fingerprint")

        reason = None
        if campaign in (None, ""):
            reason = "missing_campaign_id"
        elif campaign != campaign_id:
            reason = "campaign_mismatch"
        elif camera_index is None:
            reason = "missing_camera_index"
        elif camera_index != 0:
            reason = "wrong_camera_index"
        elif fingerprint in (None, ""):
            reason = "missing_acquisition_fingerprint"
        elif canonical_fingerprint and str(fingerprint) != canonical_fingerprint:
            reason = "acquisition_fingerprint_drift"

        if reason:
            excluded.append({**row, "exclusion_reason": reason})
        else:
            accepted.append(row)

    return accepted, excluded


def _to_float(value: object | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object | None) -> int | None:
    number = _to_float(value)
    if number is None:
        return None
    return int(number)


def _to_bool(value: object | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.fmean(values)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.median(values)


def _format_number(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/d"
    return f"{value:.{digits}f}"


def _format_ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "n/d"
    return f"{numerator / denominator:.3f}"


def _expected_pulses(ack: str) -> int | None:
    match = ACK_COUNT_PATTERN.search(ack or "")
    if not match:
        return None
    return int(match.group("count"))


def _bounded_detection_probability(detection_events: int, expected_pulses: int) -> tuple[int, float | None]:
    if expected_pulses <= 0:
        return detection_events, None
    bounded_events = min(detection_events, expected_pulses)
    return bounded_events, bounded_events / expected_pulses


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    if not rows:
        return "_Sin filas disponibles._"
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, divider, *body])


def _write_markdown(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def generate_camera0_threshold_artifacts(
    input_rows: list[dict[str, object]],
    studies_dir: Path,
    campaign_id: str = CAMERA0_THRESHOLD_CAMPAIGN_ID,
    camera_index: int = 0,
) -> dict[str, object]:
    ensure_directory(studies_dir)
    presentation_dir = studies_dir.parent / "presentation" if studies_dir.name == "studies" else studies_dir
    plots_dir = presentation_dir / "plots"
    ensure_directory(plots_dir)

    accepted_rows, excluded_rows = filter_camera0_campaign_rows(input_rows, campaign_id=campaign_id)
    validation = validate_camera0_plan_rows(accepted_rows)

    per_pulse_rows: list[dict[str, object]] = []
    duty_counts: defaultdict[int, dict[str, int]] = defaultdict(lambda: {"detected": 0, "total": 0})
    for row in accepted_rows:
        duty = _normalize_int(row.get("duty"))
        if duty is None:
            continue
        detected_any = _to_bool(row.get("detected_any"))
        duty_counts[duty]["total"] += 1
        if detected_any:
            duty_counts[duty]["detected"] += 1
        per_pulse_rows.append(
            {
                "campaign_id": campaign_id,
                "run_id": row.get("run_id", ""),
                "camera_index": camera_index,
                "duty": duty,
                "pulse_index": _normalize_int(row.get("pulse_index")) or 0,
                "detected_any": str(detected_any).lower(),
                "detected_frames": _normalize_int(row.get("detected_frames")) or 0,
                "detection_events": _normalize_int(row.get("detection_events")) or 0,
                "expected_pulses": _normalize_int(row.get("expected_pulses")) or 1,
                "block_id": _normalize_int(row.get("block_id")) or 0,
                "block_order": _normalize_int(row.get("block_order")) or 0,
                "is_dark_control": str(duty == 0).lower(),
                "is_positive_control": str(duty in REQUIRED_CAMERA0_POSITIVE_CONTROLS).lower(),
                "acquisition_fingerprint": row.get("acquisition_fingerprint", ""),
            }
        )

    by_duty_rows: list[dict[str, object]] = []
    threshold_input: list[dict[str, int]] = []
    for duty in sorted(duty_counts):
        detected = int(duty_counts[duty]["detected"])
        total = int(duty_counts[duty]["total"])
        low, high = wilson_interval(detected, total)
        threshold_input.append({"duty": duty, "detected": detected, "total": total})
        by_duty_rows.append(
            {
                "campaign_id": campaign_id,
                "camera_index": camera_index,
                "duty": duty,
                "n": total,
                "detected": detected,
                "detection_rate": round(detected / total, 6) if total else 0.0,
                "wilson_low_95": round(low, 6),
                "wilson_high_95": round(high, 6),
            }
        )

    threshold_point = estimate_detection_thresholds(threshold_input)
    threshold_boot = bootstrap_threshold_estimates(threshold_input)
    threshold_rows = [
        {
            "campaign_id": campaign_id,
            "camera_index": camera_index,
            "duty50": round(float(threshold_point["duty50"]), 6),
            "duty90": round(float(threshold_point["duty90"]), 6),
            "duty95": round(float(threshold_point["duty95"]), 6),
            "duty50_ci_low": round(float(threshold_boot["duty50"]["low"]), 6),
            "duty50_ci_high": round(float(threshold_boot["duty50"]["high"]), 6),
            "duty90_ci_low": round(float(threshold_boot["duty90"]["low"]), 6),
            "duty90_ci_high": round(float(threshold_boot["duty90"]["high"]), 6),
            "duty95_ci_low": round(float(threshold_boot["duty95"]["low"]), 6),
            "duty95_ci_high": round(float(threshold_boot["duty95"]["high"]), 6),
        }
    ]

    validation_rows = [
        {
            "campaign_id": campaign_id,
            "camera_index": camera_index,
            "is_compliant": str(validation["is_compliant"]).lower(),
            "missing_duties": ",".join(str(d) for d in validation["missing_duties"]),
            "under_replicated_duties": ",".join(str(d) for d in validation["under_replicated_duties"]),
            "below_fixed_target_duties": ",".join(str(d) for d in validation["below_fixed_target_duties"]),
            "excluded_rows": len(excluded_rows),
            "accepted_rows": len(per_pulse_rows),
            "resumen_es": "Cumple plan camera0" if validation["is_compliant"] else "Plan camera0 incompleto",
        }
    ]

    per_pulse_path = studies_dir / "camera0_intensity_per_pulse.csv"
    by_duty_path = studies_dir / "camera0_intensity_by_duty_wilson.csv"
    threshold_path = studies_dir / "camera0_threshold_estimates.csv"
    validation_path = studies_dir / "camera0_validation_report.csv"
    ci_plot_path = plots_dir / "camera0_duty_detection_ci.png"
    bootstrap_plot_path = plots_dir / "camera0_threshold_bootstrap.png"
    summary_path = presentation_dir / "camera0_intensity_threshold_summary.md"
    write_csv(per_pulse_path, per_pulse_rows)
    write_csv(by_duty_path, by_duty_rows)
    write_csv(threshold_path, threshold_rows)
    write_csv(validation_path, validation_rows)
    _write_camera0_threshold_plots(by_duty_rows, threshold_rows[0], ci_plot_path, bootstrap_plot_path)
    _write_camera0_threshold_summary(summary_path, ci_plot_path, bootstrap_plot_path, validation_rows[0], threshold_rows[0])

    return {
        "accepted_rows": len(per_pulse_rows),
        "excluded_rows": len(excluded_rows),
        "paths": {
            "camera0_intensity_per_pulse": str(per_pulse_path),
            "camera0_intensity_by_duty_wilson": str(by_duty_path),
            "camera0_threshold_estimates": str(threshold_path),
            "camera0_validation_report": str(validation_path),
            "camera0_duty_detection_ci_plot": str(ci_plot_path),
            "camera0_threshold_bootstrap_plot": str(bootstrap_plot_path),
            "camera0_intensity_threshold_summary": str(summary_path),
        },
    }


def _write_camera0_threshold_plots(
    by_duty_rows: list[dict[str, object]],
    threshold_row: dict[str, object],
    ci_plot_path: Path,
    bootstrap_plot_path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    duties = [int(row["duty"]) for row in by_duty_rows]
    rates = [float(row["detection_rate"]) for row in by_duty_rows]
    lows = [float(row["wilson_low_95"]) for row in by_duty_rows]
    highs = [float(row["wilson_high_95"]) for row in by_duty_rows]
    lower_errors = [max(0.0, rate - low) for rate, low in zip(rates, lows)]
    upper_errors = [max(0.0, high - rate) for rate, high in zip(rates, highs)]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.errorbar(duties, rates, yerr=[lower_errors, upper_errors], fmt="o-", capsize=4)
    ax.set_title("Detección camera0 por duty")
    ax.set_xlabel("Duty LED")
    ax.set_ylabel("Probabilidad de detección")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(ci_plot_path, dpi=150)
    plt.close(fig)

    labels = ["duty50", "duty90", "duty95"]
    centers = [float(threshold_row[label]) for label in labels]
    lows = [float(threshold_row[f"{label}_ci_low"]) for label in labels]
    highs = [float(threshold_row[f"{label}_ci_high"]) for label in labels]
    lower_errors = [max(0.0, center - low) for center, low in zip(centers, lows)]
    upper_errors = [max(0.0, high - center) for center, high in zip(centers, highs)]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(labels, centers, yerr=[lower_errors, upper_errors], fmt="o", capsize=5)
    ax.set_title("Umbrales estimados camera0")
    ax.set_xlabel("Estimador")
    ax.set_ylabel("Duty LED")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(bootstrap_plot_path, dpi=150)
    plt.close(fig)


def _write_camera0_threshold_summary(
    summary_path: Path,
    ci_plot_path: Path,
    bootstrap_plot_path: Path,
    validation_row: dict[str, object],
    threshold_row: dict[str, object],
) -> None:
    content = "\n".join(
        [
            "# Resumen de umbral de intensidad camera0",
            "",
            "## Análisis estadístico",
            "",
            "Este resumen reporta detectabilidad por duty con barras de error Wilson 95% y estimadores bootstrap para duty50/duty90/duty95.",
            "",
            f"- Estado de validación: `{validation_row.get('resumen_es', '')}`",
            f"- duty50: `{threshold_row.get('duty50')}`",
            f"- duty90: `{threshold_row.get('duty90')}`",
            f"- duty95: `{threshold_row.get('duty95')}`",
            "",
            "## Plots requeridos",
            "",
            f"- `{ci_plot_path.name}`",
            f"- `{bootstrap_plot_path.name}`",
            "",
        ]
    )
    _write_markdown(summary_path, content)


def collect_webcam_intensity(repo_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    data_dir = repo_root / "data" / "webcam"
    observation_rows: list[dict[str, object]] = []
    by_duty: defaultdict[int, list[dict[str, object]]] = defaultdict(list)
    for csv_path in sorted(data_dir.glob("led_intensity*_sweep_*.csv")):
        for row in read_csv_rows(csv_path):
            duty = _to_int(row.get("duty"))
            detection_events = _to_int(row.get("detection_events")) or 0
            detected_frames = _to_int(row.get("detected_frames")) or 0
            expected_pulses = _expected_pulses(row.get("led_ack", "")) or 0
            bounded_events, probability = _bounded_detection_probability(detection_events, expected_pulses)
            observation = {
                "study_family": "webcam_intensity_sweep",
                "source_run": csv_path.stem,
                "duty": duty or "",
                "intensity_percent": _to_float(row.get("intensity_percent")) or "",
                "expected_pulses": expected_pulses,
                "detection_events": detection_events,
                "bounded_detected_pulses": bounded_events,
                "detected_frames": detected_frames,
                "detection_probability": round(probability, 6) if probability is not None else "",
                "detected_any": str(detection_events > 0).lower(),
                "event_overcount_flag": str(expected_pulses > 0 and detection_events > expected_pulses).lower(),
                "measured_fps": _to_float(row.get("measured_fps")) or "",
                "metrics_csv": row.get("csv", ""),
            }
            observation_rows.append(observation)
            if duty is not None:
                by_duty[duty].append(observation)

    summary_rows: list[dict[str, object]] = []
    for duty in sorted(by_duty):
        rows = by_duty[duty]
        probabilities = [float(row["detection_probability"]) for row in rows if row.get("detection_probability", "") != ""]
        summary_rows.append(
            {
                "duty": duty,
                "replicates": len(rows),
                "mean_detection_probability": round(_mean(probabilities) or 0.0, 6),
                "median_detection_probability": round(_median(probabilities) or 0.0, 6),
                "detected_runs": sum(1 for row in rows if str(row["detected_any"]) == "true"),
                "expected_total_pulses": sum(int(row["expected_pulses"]) for row in rows),
                "detected_total_events": sum(int(row["detection_events"]) for row in rows),
                "bounded_detected_total": sum(int(row["bounded_detected_pulses"]) for row in rows),
                "mean_detected_frames": round(_mean([float(row["detected_frames"]) for row in rows]) or 0.0, 3),
            }
        )
    return observation_rows, summary_rows


def collect_webcam_parameters(repo_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    data_dir = repo_root / "data" / "webcam"
    observation_rows: list[dict[str, object]] = []
    by_exposure: defaultdict[tuple[int, float], list[dict[str, object]]] = defaultdict(list)
    by_duration: defaultdict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
    for csv_path in sorted(data_dir.glob("flash_parameter*.csv")):
        for row in read_csv_rows(csv_path):
            duty = _to_int(row.get("duty"))
            duration_ms = _to_int(row.get("duration_ms"))
            exposure = _to_float(row.get("exposure"))
            detection_events = _to_int(row.get("detection_events")) or 0
            expected_pulses = _expected_pulses(row.get("led_ack", "")) or 0
            bounded_events, probability = _bounded_detection_probability(detection_events, expected_pulses)
            observation = {
                "study_family": "webcam_parameter_sweep",
                "source_run": csv_path.stem,
                "sweep": row.get("sweep", ""),
                "value": _to_float(row.get("value")) or "",
                "duty": duty or "",
                "duration_ms": duration_ms or "",
                "exposure": exposure or "",
                "expected_pulses": expected_pulses,
                "detection_events": detection_events,
                "bounded_detected_pulses": bounded_events,
                "detected_frames": _to_int(row.get("detected_frames")) or 0,
                "detection_probability": round(probability, 6) if probability is not None else "",
                "detected_any": str(detection_events > 0).lower(),
                "event_overcount_flag": str(expected_pulses > 0 and detection_events > expected_pulses).lower(),
                "measured_fps": _to_float(row.get("measured_fps")) or "",
                "metrics_csv": row.get("csv", ""),
            }
            observation_rows.append(observation)
            if row.get("sweep") == "exposure" and duty is not None and exposure is not None:
                by_exposure[(duty, exposure)].append(observation)
            if row.get("sweep") == "duration_ms" and duty is not None and duration_ms is not None:
                by_duration[(duty, duration_ms)].append(observation)

    exposure_rows: list[dict[str, object]] = []
    for (duty, exposure) in sorted(by_exposure):
        rows = by_exposure[(duty, exposure)]
        probabilities = [float(row["detection_probability"]) for row in rows if row.get("detection_probability", "") != ""]
        exposure_rows.append(
            {
                "duty": duty,
                "exposure": exposure,
                "replicates": len(rows),
                "mean_detection_probability": round(_mean(probabilities) or 0.0, 6),
                "median_detection_probability": round(_median(probabilities) or 0.0, 6),
                "detected_total_events": sum(int(row["detection_events"]) for row in rows),
                "bounded_detected_total": sum(int(row["bounded_detected_pulses"]) for row in rows),
                "expected_total_pulses": sum(int(row["expected_pulses"]) for row in rows),
            }
        )

    duration_rows: list[dict[str, object]] = []
    for (duty, duration_ms) in sorted(by_duration):
        rows = by_duration[(duty, duration_ms)]
        probabilities = [float(row["detection_probability"]) for row in rows if row.get("detection_probability", "") != ""]
        duration_rows.append(
            {
                "duty": duty,
                "duration_ms": duration_ms,
                "replicates": len(rows),
                "mean_detection_probability": round(_mean(probabilities) or 0.0, 6),
                "median_detection_probability": round(_median(probabilities) or 0.0, 6),
                "detected_total_events": sum(int(row["detection_events"]) for row in rows),
                "bounded_detected_total": sum(int(row["bounded_detected_pulses"]) for row in rows),
                "expected_total_pulses": sum(int(row["expected_pulses"]) for row in rows),
            }
        )

    return observation_rows, exposure_rows, duration_rows


def _parse_op598_summary(summary_path: Path) -> dict[str, object] | None:
    values = read_key_value_csv(summary_path)
    if not values:
        return None
    run_id = summary_path.name.replace("_summary.csv", "")
    command = str(values.get("command", ""))
    if "pulse_profile" in run_id:
        command_type = "pulse_profile"
    elif "train_profile" in run_id:
        command_type = "train_profile"
    elif "sample" in run_id:
        command_type = "sample"
    else:
        command_type = "unknown"
    peak_adc = _to_float(values.get("peak_adc"))
    baseline_adc = _to_float(values.get("baseline_adc"))
    return {
        "run_id": run_id,
        "command": command,
        "command_type": command_type,
        "duration_ms": _to_int(values.get("metadata.duration_ms")) or "",
        "duty": _to_int(values.get("metadata.duty")) or "",
        "period_ms": _to_int(values.get("metadata.period_ms")) or "",
        "count": _to_int(values.get("metadata.count")) or _to_int(values.get("pulse_count")) or 0,
        "sample_count": _to_int(values.get("sample_count")) or 0,
        "baseline_adc": baseline_adc or "",
        "peak_adc": peak_adc or "",
        "peak_minus_baseline": round((peak_adc - baseline_adc), 6) if peak_adc is not None and baseline_adc is not None else "",
        "pulse_width_ms": _to_float(values.get("pulse_width_ms")) or "",
        "rise_time_ms": _to_float(values.get("rise_time_ms")) or "",
        "fall_time_ms": _to_float(values.get("fall_time_ms")) or "",
        "threshold_crossing_ms": _to_float(values.get("threshold_crossing_ms")) or "",
        "sample_interval_avg_ms": _to_float(values.get("sample_interval_avg_ms")) or "",
        "saturation_flag": str((peak_adc or 0.0) >= 4095.0).lower(),
        "source_summary": str(summary_path),
    }


def collect_op598_characterization(repo_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    data_dir = repo_root / "data" / "op598"
    characterization_doc = data_dir / "op598_characterization_20260522_1524.md"
    canonical_stems: set[str] = set()
    if characterization_doc.exists():
        for match in re.findall(r"data/op598/(?P<stem>[^`/]+)\.csv", characterization_doc.read_text(encoding="utf-8")):
            canonical_stems.add(match)
    summary_paths = sorted(data_dir.glob("*_summary.csv"))
    if canonical_stems:
        summary_paths = [path for path in summary_paths if path.name.replace("_summary.csv", "") in canonical_stems]
    run_rows = [row for row in (_parse_op598_summary(path) for path in summary_paths) if row]

    by_duration_groups: defaultdict[int, list[dict[str, object]]] = defaultdict(list)
    by_duty_groups: defaultdict[int, list[dict[str, object]]] = defaultdict(list)
    for row in run_rows:
        if row["command_type"] == "pulse_profile" and row["duty"] == 1023 and row["duration_ms"] != "":
            by_duration_groups[int(row["duration_ms"])] .append(row)
        if row["command_type"] == "pulse_profile" and row["duration_ms"] == 200 and row["duty"] != "":
            by_duty_groups[int(row["duty"])] .append(row)

    by_duration_rows: list[dict[str, object]] = []
    for duration_ms in sorted(by_duration_groups):
        rows = by_duration_groups[duration_ms]
        peaks = [float(row["peak_adc"]) for row in rows if row["peak_adc"] != ""]
        widths = [float(row["pulse_width_ms"]) for row in rows if row["pulse_width_ms"] != ""]
        by_duration_rows.append(
            {
                "duration_ms": duration_ms,
                "replicates": len(rows),
                "mean_peak_adc": round(_mean(peaks) or 0.0, 6),
                "median_peak_adc": round(_median(peaks) or 0.0, 6),
                "mean_pulse_width_ms": round(_mean(widths) or 0.0, 6),
                "any_saturated": str(any(str(row["saturation_flag"]) == "true" for row in rows)).lower(),
            }
        )

    by_duty_rows: list[dict[str, object]] = []
    for duty in sorted(by_duty_groups):
        rows = by_duty_groups[duty]
        peaks = [float(row["peak_adc"]) for row in rows if row["peak_adc"] != ""]
        deltas = [float(row["peak_minus_baseline"]) for row in rows if row["peak_minus_baseline"] != ""]
        by_duty_rows.append(
            {
                "duty": duty,
                "replicates": len(rows),
                "mean_peak_adc": round(_mean(peaks) or 0.0, 6),
                "mean_peak_minus_baseline": round(_mean(deltas) or 0.0, 6),
                "all_saturated": str(all(str(row["saturation_flag"]) == "true" for row in rows)).lower(),
                "any_saturated": str(any(str(row["saturation_flag"]) == "true" for row in rows)).lower(),
            }
        )

    return run_rows, by_duration_rows, by_duty_rows


def collect_dual_random_train(
    repo_root: Path,
    campaign_id: str | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    for coincidence_path in sorted(repo_root.glob("data/dual_experiments/**/coincidence_table.csv")):
        run_dir = coincidence_path.parent
        run_id = run_dir.name
        if not DUAL_RUN_PATTERN.fullmatch(run_id):
            continue
        summary_path = run_dir / "dual_summary.csv"
        if not summary_path.exists():
            continue
        summary = read_key_value_csv(summary_path)
        if summary.get("mode") != "random-train":
            continue
        coincidence_rows = read_csv_rows(coincidence_path)
        if not coincidence_rows:
            continue

        total_pulses = len(coincidence_rows)
        covered_rows = [row for row in coincidence_rows if (_to_int(row.get("window_frame_count")) or 0) > 0]
        detected_rows = [row for row in covered_rows if _to_bool(row.get("matched_frame_detected"))]
        detected_window_rows = [row for row in covered_rows if _to_bool(row.get("detected_in_window"))]
        all_offsets = [_to_float(row.get("matched_frame_dt_ms")) for row in covered_rows]
        all_offsets = [value for value in all_offsets if value is not None]
        detected_offsets = [_to_float(row.get("matched_frame_dt_ms")) for row in detected_rows]
        detected_offsets = [value for value in detected_offsets if value is not None]
        covered_pulses = len(covered_rows)
        matched_detected = len(detected_rows)
        run_row = {
            "run_id": run_id,
            "variant": str(run_dir.parent.name),
            "campaign_id": summary.get("production.campaign_id", ""),
            "mount_context": summary.get("production.mount_context", ""),
            "run_intent": summary.get("production.run_intent", ""),
            "dark_control_ref": summary.get("production.dark_control_ref", ""),
            "run_index": _to_int(summary.get("production.run_index")) or "",
            "duty": _to_int(summary.get("op598.metadata.duty")) or "",
            "duration_ms": _to_int(summary.get("op598.metadata.duration_ms")) or "",
            "command_count": _to_int(summary.get("op598.metadata.count")) or total_pulses,
            "pulse_count_table": total_pulses,
            "covered_pulses": covered_pulses,
            "coverage_fraction": round((covered_pulses / total_pulses), 6) if total_pulses else "",
            "detected_windows": len(detected_window_rows),
            "matched_detected": matched_detected,
            "coincidence_success_rate_windowed": round((matched_detected / covered_pulses), 6) if covered_pulses else "",
            "coincidence_success_rate_all_pulses": round((matched_detected / total_pulses), 6) if total_pulses else "",
            "mean_offset_ms_windowed": round(_mean(all_offsets) or 0.0, 6) if all_offsets else "",
            "median_offset_ms_windowed": round(_median(all_offsets) or 0.0, 6) if all_offsets else "",
            "mean_offset_ms_detected": round(_mean(detected_offsets) or 0.0, 6) if detected_offsets else "",
            "median_offset_ms_detected": round(_median(detected_offsets) or 0.0, 6) if detected_offsets else "",
            "limited_coverage": str(covered_pulses < total_pulses).lower(),
            "source_summary": _relative(summary_path, repo_root),
            "source_coincidence": _relative(coincidence_path, repo_root),
        }
        if campaign_id and run_row["campaign_id"] != campaign_id:
            continue
        rows.append(run_row)

    fully_covered = [row for row in rows if str(row["limited_coverage"]) == "false"]
    summary_rows = [
        {
            "subset": "all_runs",
            "run_count": len(rows),
            "mean_windowed_success_rate": round(_mean([float(row["coincidence_success_rate_windowed"]) for row in rows if row["coincidence_success_rate_windowed"] != ""]) or 0.0, 6),
            "mean_all_pulse_success_rate": round(_mean([float(row["coincidence_success_rate_all_pulses"]) for row in rows if row["coincidence_success_rate_all_pulses"] != ""]) or 0.0, 6),
        },
        {
            "subset": "fully_covered_runs",
            "run_count": len(fully_covered),
            "mean_windowed_success_rate": round(_mean([float(row["coincidence_success_rate_windowed"]) for row in fully_covered if row["coincidence_success_rate_windowed"] != ""]) or 0.0, 6),
            "mean_all_pulse_success_rate": round(_mean([float(row["coincidence_success_rate_all_pulses"]) for row in fully_covered if row["coincidence_success_rate_all_pulses"] != ""]) or 0.0, 6),
        },
    ]
    return rows, summary_rows


def _webcam_intensity_markdown(summary_rows: list[dict[str, object]]) -> str:
    threshold_row = next((row for row in summary_rows if float(row["mean_detection_probability"]) >= 0.5), None)
    findings = []
    pulse_counts = [
        int(row["expected_total_pulses"])
        for row in summary_rows
        if str(row.get("expected_total_pulses", "")).isdigit()
    ]
    pulse_limit = (
        f"Cada duty agrega hasta `{min(pulse_counts)}`-`{max(pulse_counts)}` pulsos esperados según `led_ack`."
        if pulse_counts and min(pulse_counts) != max(pulse_counts)
        else f"Cada duty agrega `{pulse_counts[0]}` pulsos esperados según `led_ack`."
        if pulse_counts
        else "La cantidad de pulsos esperados no está disponible en los CSV fuente."
    )
    if threshold_row:
        findings.append(f"- La webcam empieza a mostrar deteccion consistente desde `duty {threshold_row['duty']}` en estas corridas heredadas.")
    if summary_rows:
        best_row = max(summary_rows, key=lambda row: float(row["mean_detection_probability"]))
        findings.append(
            f"- El mejor promedio de deteccion en esta familia fue `p={best_row['mean_detection_probability']}` en `duty {best_row['duty']}`."
        )
    return "\n".join(
        [
            "# Resumen de estudio: barrido de intensidad webcam",
            "",
            "## Hallazgos",
            *findings,
            "",
            "## Tabla agregada por duty",
            _markdown_table(
                summary_rows,
                [
                    "duty",
                    "replicates",
                    "mean_detection_probability",
                    "median_detection_probability",
                    "bounded_detected_total",
                    "detected_total_events",
                    "expected_total_pulses",
                ],
            ),
            "",
            "## Limitaciones",
            f"- {pulse_limit} La probabilidad usa eventos detectados acotados por pulsos esperados; no identifica qué pulso individual disparó cada detección.",
            "- La métrica es detectabilidad de la cadena webcam + umbral actual, no radiometría del LED.",
        ]
    )


def _webcam_parameters_markdown(exposure_rows: list[dict[str, object]], duration_rows: list[dict[str, object]]) -> str:
    return "\n".join(
        [
            "# Resumen de estudio: barrido de parámetros webcam",
            "",
            "## Hallazgos",
            "- La exposición muestra comportamiento útil pero no estrictamente monótono en el régimen de duty bajo; el sistema todavía es sensible al umbral y al muestreo discreto por frames.",
            "- La duración del pulso sí muestra una tendencia más clara: pulsos de `5-20 ms` quedan mayormente invisibles para la webcam en estas condiciones, mientras que a partir de `50-100 ms` la detectabilidad mejora.",
            "",
            "## Agregado por exposición",
            _markdown_table(
                exposure_rows,
                [
                    "duty",
                    "exposure",
                    "replicates",
                    "mean_detection_probability",
                    "bounded_detected_total",
                    "detected_total_events",
                    "expected_total_pulses",
                ],
            ),
            "",
            "## Agregado por duración",
            _markdown_table(
                duration_rows,
                [
                    "duty",
                    "duration_ms",
                    "replicates",
                    "mean_detection_probability",
                    "bounded_detected_total",
                    "detected_total_events",
                    "expected_total_pulses",
                ],
            ),
            "",
            "## Limitaciones",
            "- Este estudio mezcla al menos dos duties (`6` y `8`), así que exposición y duración deben leerse condicionadas por duty, no como una curva global única.",
            "- Cada condición también tiene solo `3` pulsos esperados, así que la granularidad de probabilidad es gruesa (`0`, `1/3`, `2/3`, `1`).",
            "- En algunos casos `detection_events` crudo supera los pulsos comandados por sobre-segmentación; la probabilidad se acota usando `min(eventos, pulsos esperados)`.",
        ]
    )


def _op598_markdown(duration_rows: list[dict[str, object]], duty_rows: list[dict[str, object]], run_rows: list[dict[str, object]]) -> str:
    sample_intervals = [float(row["sample_interval_avg_ms"]) for row in run_rows if row["sample_interval_avg_ms"] != ""]
    saturated_duties = [str(row["duty"]) for row in duty_rows if str(row["any_saturated"]) == "true"]
    return "\n".join(
        [
            "# Resumen de estudio: caracterización OP598",
            "",
            "## Hallazgos",
            f"- El intervalo de muestreo efectivo del camino OP598 se mantiene alrededor de `{_format_number(_mean(sample_intervals), 3)} ms`, lejos del `1 ms` solicitado.",
            f"- Hay saturación clara en duties altos: `{', '.join(saturated_duties) if saturated_duties else 'ninguno'}`.",
            "- El rango bajo (`duty 8-32`) es el más interpretable para comparar amplitud sin pegarse inmediatamente al techo ADC.",
            "",
            "## Agregado por duración a duty 1023",
            _markdown_table(
                duration_rows,
                ["duration_ms", "replicates", "mean_peak_adc", "mean_pulse_width_ms", "any_saturated"],
            ),
            "",
            "## Agregado por duty a duración 200 ms",
            _markdown_table(
                duty_rows,
                ["duty", "replicates", "mean_peak_adc", "mean_peak_minus_baseline", "all_saturated", "any_saturated"],
            ),
            "",
            "## Limitaciones",
            "- Esto caracteriza la cadena montada `LED + optica + OP598 + ADC + MicroPython`; no es una medición intrínseca ultrarrápida del fototransistor.",
            "- Las corridas saturadas sirven para detectabilidad, pero NO para inferir linealidad de intensidad.",
        ]
    )


def _dual_markdown(run_rows: list[dict[str, object]], summary_rows: list[dict[str, object]]) -> str:
    best_row = max(
        [row for row in run_rows if row.get("coincidence_success_rate_windowed", "") != ""],
        key=lambda row: float(row["coincidence_success_rate_windowed"]),
        default=None,
    )
    limited_count = sum(1 for row in run_rows if str(row["limited_coverage"]) == "true")
    findings = [
        "- La coincidencia dual ya es cuantificable corrida por corrida usando las ventanas reconstruidas alrededor del ancla OP598.",
        f"- Corridas con cobertura webcam incompleta: `{limited_count}` de `{len(run_rows)}`.",
    ]
    if best_row:
        findings.append(
            f"- La mejor corrida cubierta alcanzó `p={best_row['coincidence_success_rate_windowed']}` en `run {best_row['run_id']}`."
        )
    return "\n".join(
        [
            "# Resumen de estudio: coincidencia dual random-train",
            "",
            "## Hallazgos",
            *findings,
            "",
            "## Resumen global",
            _markdown_table(summary_rows, ["subset", "run_count", "mean_windowed_success_rate", "mean_all_pulse_success_rate"]),
            "",
            "## Corridas por run",
            _markdown_table(
                run_rows,
                [
                    "run_id",
                    "variant",
                    "command_count",
                    "covered_pulses",
                    "coverage_fraction",
                    "matched_detected",
                    "coincidence_success_rate_windowed",
                    "mean_offset_ms_detected",
                    "limited_coverage",
                ],
            ),
            "",
            "## Limitaciones",
            "- Varias corridas largas terminan con cobertura webcam parcial; en esos casos la tasa sobre todos los pulsos subestima la coincidencia real porque el video no cubrió toda la secuencia.",
            "- Los offsets deben interpretarse sobre pulsos detectados o sobre ventanas cubiertas; promedios globales heredados pueden quedar sesgados por frames faltantes al final.",
        ]
    )


def _overview_markdown(plot_paths: list[str]) -> str:
    plot_lines = [f"- `{path}`" for path in plot_paths] if plot_paths else ["- No se generaron plots PNG en este entorno."]
    return "\n".join(
        [
            "# Resumen offline para presentación",
            "",
            "## Estudios construidos",
            "- Barrido de intensidad webcam.",
            "- Barrido de parámetros webcam (exposición y duración).",
            "- Caracterización OP598 con énfasis en saturación y tiempos efectivos.",
            "- Resumen de coincidencia dual random-train por corrida.",
            "",
            "## Artefactos de presentación",
            *plot_lines,
        ]
    )


def build_study_outputs(
    repo_root: Path,
    studies_dir: Path,
    presentation_dir: Path,
    campaign_id: str | None = None,
) -> dict[str, object]:
    ensure_directory(studies_dir)
    ensure_directory(presentation_dir)

    intensity_observations, intensity_summary = collect_webcam_intensity(repo_root)
    parameter_observations, exposure_summary, duration_summary = collect_webcam_parameters(repo_root)
    op598_runs, op598_duration, op598_duty = collect_op598_characterization(repo_root)
    dual_runs, dual_summary = collect_dual_random_train(repo_root, campaign_id=campaign_id)

    write_csv(studies_dir / "webcam_intensity_observations.csv", intensity_observations)
    write_csv(studies_dir / "webcam_intensity_by_duty.csv", intensity_summary)
    write_csv(studies_dir / "webcam_parameter_observations.csv", parameter_observations)
    write_csv(studies_dir / "webcam_parameter_by_exposure.csv", exposure_summary)
    write_csv(studies_dir / "webcam_parameter_by_duration.csv", duration_summary)
    write_csv(studies_dir / "op598_characterization_runs.csv", op598_runs)
    write_csv(studies_dir / "op598_characterization_by_duration.csv", op598_duration)
    write_csv(studies_dir / "op598_characterization_by_duty.csv", op598_duty)
    write_csv(studies_dir / "dual_random_train_runs.csv", dual_runs)
    write_csv(studies_dir / "dual_random_train_overall.csv", dual_summary)

    _write_markdown(presentation_dir / "webcam_intensity_summary.md", _webcam_intensity_markdown(intensity_summary))
    _write_markdown(presentation_dir / "webcam_parameter_summary.md", _webcam_parameters_markdown(exposure_summary, duration_summary))
    _write_markdown(presentation_dir / "op598_characterization_summary.md", _op598_markdown(op598_duration, op598_duty, op598_runs))
    _write_markdown(presentation_dir / "dual_random_train_summary.md", _dual_markdown(dual_runs, dual_summary))

    plot_paths = build_presentation_plots(
        presentation_dir / "plots",
        intensity_summary,
        exposure_summary,
        duration_summary,
        op598_duty,
        dual_runs,
    )
    _write_markdown(presentation_dir / "offline_study_overview.md", _overview_markdown([_relative(Path(path), repo_root) for path in plot_paths]))

    return {
        "studies_dir": str(studies_dir),
        "presentation_dir": str(presentation_dir),
        "study_outputs": [
            "webcam_intensity_by_duty",
            "webcam_parameter_by_exposure",
            "webcam_parameter_by_duration",
            "op598_characterization_by_duration",
            "op598_characterization_by_duty",
            "dual_random_train_runs",
        ],
        "plot_count": len(plot_paths),
        "plots": [_relative(Path(path), repo_root) for path in plot_paths],
        "counts": {
            "webcam_intensity_conditions": len(intensity_summary),
            "webcam_parameter_conditions_exposure": len(exposure_summary),
            "webcam_parameter_conditions_duration": len(duration_summary),
            "op598_runs": len(op598_runs),
            "dual_random_train_runs": len(dual_runs),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build offline study-level aggregations and presentation summaries.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--studies-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "derived" / "studies")
    parser.add_argument("--presentation-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "derived" / "presentation")
    parser.add_argument("--campaign-id", help="Optional campaign filter for dual random-train aggregation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_study_outputs(
        repo_root=args.repo_root.resolve(),
        studies_dir=args.studies_dir.resolve(),
        presentation_dir=args.presentation_dir.resolve(),
        campaign_id=args.campaign_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
