"""
Coordinate the webcam detector and OP598 capture in one experiment run.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    import cv2
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit(
        "OpenCV is not installed. Run: python -m pip install -r requirements.txt"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DETECTOR = PROJECT_ROOT / "tools" / "webcam_flash_detector.py"
OP598_CAPTURE = PROJECT_ROOT / "tools" / "capture_op598_response.py"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "dual_experiments"


def display_path(path: Path) -> str:
    if path.is_absolute():
        try:
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(path)
    return str(path)


def build_output_paths(root: Path, mode: str) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = root / f"{mode}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir = run_dir / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_dir": run_dir,
        "manifest": run_dir / "manifest.json",
        "webcam_csv": run_dir / "webcam_metrics.csv",
        "webcam_video": run_dir / "webcam_capture.avi",
        "webcam_frames": run_dir / "webcam_frames",
        "op598_dir": run_dir / "op598",
        "pulse_events_csv": run_dir / "pulse_events.csv",
        "coincidence_csv": run_dir / "coincidence_table.csv",
        "summary_csv": run_dir / "dual_summary.csv",
        "summary_md": run_dir / "dual_summary.md",
        "visuals_dir": visuals_dir,
        "average_frame": visuals_dir / "average_frame.png",
        "heatmap": visuals_dir / "coincidence_heatmap.png",
        "pulse_strip": visuals_dir / "pulse_strip.png",
    }


def run_subprocess(command: list[str]) -> subprocess.Popen[str]:
    return subprocess.Popen(command, stdout=sys.stdout, stderr=sys.stderr, text=True)


def nominal_capture_seconds(args: argparse.Namespace) -> float:
    if args.mode == "pulse":
        profile_seconds = (args.pre_ms + args.duration_ms + args.post_ms) / 1000.0
    elif args.mode == "train":
        profile_seconds = (
            args.pre_ms + args.post_ms + max(0, args.count - 1) * args.period_ms + args.duration_ms
        ) / 1000.0
    else:
        profile_seconds = (
            args.pre_ms + args.post_ms + max(0, args.count - 1) * args.max_period_ms + args.duration_ms
        ) / 1000.0
    return args.warmup + args.calibration + args.trigger_delay + profile_seconds + args.tail_seconds


def detector_command(args: argparse.Namespace, paths: dict[str, Path]) -> list[str]:
    command = [
        sys.executable,
        str(DETECTOR),
        "--index",
        str(args.index),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--fps",
        str(args.fps),
        "--fourcc",
        args.fourcc,
        "--seconds",
        str(nominal_capture_seconds(args)),
        "--warmup",
        str(args.warmup),
        "--calibration",
        str(args.calibration),
        "--metric",
        args.metric,
        "--threshold-delta",
        str(args.threshold_delta),
        "--sigma-multiplier",
        str(args.sigma_multiplier),
        "--output",
        str(paths["webcam_csv"]),
        "--frames-dir",
        str(paths["webcam_frames"]),
        "--video-output",
        str(paths["webcam_video"]),
    ]
    if args.raw:
        command.append("--raw")
    if args.preview:
        command.append("--preview")
    if args.save_detected_frames:
        command.append("--save-detected-frames")
    if args.auto_exposure:
        command += ["--auto-exposure", args.auto_exposure]
    if args.exposure is not None:
        command += ["--exposure", str(args.exposure)]
    if args.exposure_auto_priority is not None:
        command += ["--exposure-auto-priority", str(args.exposure_auto_priority)]
    if args.roi:
        command += ["--roi", args.roi]
    return command


def op598_command(args: argparse.Namespace, paths: dict[str, Path]) -> list[str]:
    command = [
        sys.executable,
        str(OP598_CAPTURE),
        "--port",
        args.port,
        "--baud",
        str(args.baud),
        "--output-dir",
        str(paths["op598_dir"]),
        "--threshold-fraction",
        str(args.op598_threshold_fraction),
        "--print-every",
        str(args.op598_print_every),
    ]
    if args.live_sensor_plot:
        command.append("--live-plot")
    if args.op598_verbose:
        command.append("--verbose")

    if args.mode == "pulse":
        command += [
            "pulse",
            "--duration-ms",
            str(args.duration_ms),
            "--duty",
            str(args.duty),
            "--pre-ms",
            str(args.pre_ms),
            "--post-ms",
            str(args.post_ms),
            "--sample-us",
            str(args.sample_us),
        ]
    elif args.mode == "train":
        command += [
            "train",
            "--count",
            str(args.count),
            "--period-ms",
            str(args.period_ms),
            "--duration-ms",
            str(args.duration_ms),
            "--duty",
            str(args.duty),
            "--pre-ms",
            str(args.pre_ms),
            "--post-ms",
            str(args.post_ms),
            "--sample-us",
            str(args.sample_us),
        ]
    else:
        command += [
            "random-train",
            "--count",
            str(args.count),
            "--min-period-ms",
            str(args.min_period_ms),
            "--max-period-ms",
            str(args.max_period_ms),
            "--duration-ms",
            str(args.duration_ms),
            "--duty",
            str(args.duty),
            "--pre-ms",
            str(args.pre_ms),
            "--post-ms",
            str(args.post_ms),
            "--sample-us",
            str(args.sample_us),
        ]
    return command


def contiguous_event_count(values: list[int]) -> int:
    count = 0
    previous = 0
    for value in values:
        if value and not previous:
            count += 1
        previous = value
    return count


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def read_webcam_rows(csv_path: Path) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for row in read_csv_rows(csv_path):
        rows.append(
            {
                "timestamp_s": float(row.get("timestamp_s", 0.0)),
                "perf_counter_s": float(row.get("perf_counter_s", 0.0)),
                "frame_index": int(row.get("frame_index", 0)),
                "mean": float(row.get("mean", 0.0)),
                "max": float(row.get("max", 0.0)),
                "p99": float(row.get("p99", 0.0)),
                "threshold": float(row.get("threshold", 0.0)),
                "detected": int(row.get("detected", 0)),
            }
        )
    return rows


def read_webcam_summary(csv_path: Path) -> dict[str, float | int]:
    rows = read_webcam_rows(csv_path)
    detections = [int(row["detected"]) for row in rows]
    fps = 0.0
    if len(rows) >= 2:
        elapsed = float(rows[-1]["timestamp_s"]) - float(rows[0]["timestamp_s"])
        fps = (len(rows) - 1) / elapsed if elapsed > 0 else 0.0
    return {
        "frames": len(rows),
        "detected_frames": sum(detections),
        "detection_events": contiguous_event_count(detections),
        "measured_fps": fps,
    }


def latest_op598_files(op598_dir: Path) -> dict[str, Path | None]:
    candidates = sorted(op598_dir.glob("*_summary.csv"))
    summary_csv = candidates[-1] if candidates else None
    plot_candidates = sorted(op598_dir.glob("*.png"))
    csv_candidates = [path for path in op598_dir.glob("*.csv") if not path.name.endswith("_summary.csv")]
    summary_md_candidates = sorted(op598_dir.glob("*_summary.md"))
    log_candidates = sorted(op598_dir.glob("*.log"))
    return {
        "summary_csv": summary_csv,
        "plot": plot_candidates[-1] if plot_candidates else None,
        "csv": sorted(csv_candidates)[-1] if csv_candidates else None,
        "summary_md": summary_md_candidates[-1] if summary_md_candidates else None,
        "log": log_candidates[-1] if log_candidates else None,
    }


def read_key_value_summary(summary_csv: Path | None) -> dict[str, str]:
    if summary_csv is None or not summary_csv.exists():
        return {}
    rows = csv.DictReader(summary_csv.open("r", encoding="utf-8", newline=""))
    return {row["field"]: row["value"] for row in rows}


def read_op598_rows(csv_path: Path | None) -> list[dict[str, float | int | str]]:
    if csv_path is None or not csv_path.exists():
        return []
    rows: list[dict[str, float | int | str]] = []
    for row in read_csv_rows(csv_path):
        rows.append(
            {
                "index": int(row.get("index", 0)),
                "t_us": int(float(row.get("t_us", 0))),
                "t_ms": float(row.get("t_ms", 0.0)),
                "adc": int(float(row.get("adc", 0))),
                "led": int(float(row.get("led", 0))),
                "phase": row.get("phase", "unknown"),
                "pulse_index": int(float(row.get("pulse_index", -1))),
            }
        )
    return rows


def compute_op598_baseline(rows: list[dict[str, float | int | str]]) -> float:
    dark_values = [
        int(row["adc"])
        for row in rows
        if int(row["led"]) == 0 and str(row["phase"]) in {"pre", "gap", "post"}
    ]
    if dark_values:
        return float(np.mean(dark_values))
    return float(np.mean([int(row["adc"]) for row in rows[: max(1, len(rows) // 10)]])) if rows else 0.0


def build_pulse_events(
    rows: list[dict[str, float | int | str]], threshold_fraction: float
) -> list[dict[str, float | int | str | bool | None]]:
    if not rows:
        return []
    baseline_adc = compute_op598_baseline(rows)
    pulse_indexes = sorted({int(row["pulse_index"]) for row in rows if int(row["pulse_index"]) >= 0})
    pulse_events: list[dict[str, float | int | str | bool | None]] = []
    for pulse_index in pulse_indexes:
        pulse_rows = [row for row in rows if int(row["pulse_index"]) == pulse_index]
        lit_rows = [row for row in pulse_rows if int(row["led"]) == 1 or str(row["phase"]) == "pulse"]
        if not pulse_rows:
            continue
        start_ms = float(min((row["t_ms"] for row in lit_rows), default=pulse_rows[0]["t_ms"]))
        end_ms = float(max((row["t_ms"] for row in lit_rows), default=pulse_rows[-1]["t_ms"]))
        peak_row = max(pulse_rows, key=lambda row: int(row["adc"]))
        peak_adc = int(peak_row["adc"])
        peak_ms = float(peak_row["t_ms"])
        threshold_adc = baseline_adc + max(0.0, peak_adc - baseline_adc) * threshold_fraction
        crossing_ms = None
        for row in pulse_rows:
            if float(row["t_ms"]) >= start_ms and int(row["adc"]) >= threshold_adc:
                crossing_ms = float(row["t_ms"])
                break
        anchor_ms = crossing_ms if crossing_ms is not None else peak_ms
        pulse_events.append(
            {
                "pulse_index": pulse_index,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": max(0.0, end_ms - start_ms),
                "anchor_ms": anchor_ms,
                "peak_ms": peak_ms,
                "peak_adc": peak_adc,
                "mean_adc": float(np.mean([int(row["adc"]) for row in pulse_rows])),
                "baseline_adc": baseline_adc,
                "threshold_adc": threshold_adc,
                "sample_count": len(pulse_rows),
                "op598_detected": peak_adc > baseline_adc,
            }
        )
    return pulse_events


def nearest_row_index(webcam_rows: list[dict[str, float | int]], target_perf_s: float) -> int | None:
    if not webcam_rows:
        return None
    return min(
        range(len(webcam_rows)),
        key=lambda index: abs(float(webcam_rows[index]["perf_counter_s"]) - target_perf_s),
    )


def build_coincidence_rows(
    args: argparse.Namespace,
    webcam_rows: list[dict[str, float | int]],
    pulse_events: list[dict[str, float | int | str | bool | None]],
    op598_summary: dict[str, str],
) -> list[dict[str, float | int | str | bool | None]]:
    if not pulse_events:
        return []

    command_sent_perf_s = float(op598_summary.get("metadata.host_command_sent_perf_counter_s", 0.0) or 0.0)
    frame_window_s = args.coincidence_window_ms / 1000.0
    coincidence_rows: list[dict[str, float | int | str | bool | None]] = []

    for pulse in pulse_events:
        anchor_ms = float(pulse["anchor_ms"] or 0.0)
        if command_sent_perf_s > 0.0:
            anchor_perf_s = command_sent_perf_s + anchor_ms / 1000.0
        else:
            anchor_perf_s = args.trigger_delay + anchor_ms / 1000.0

        nearest_index = nearest_row_index(webcam_rows, anchor_perf_s)
        nearest_row = webcam_rows[nearest_index] if nearest_index is not None else None
        window_rows = [
            row
            for row in webcam_rows
            if abs(float(row["perf_counter_s"]) - anchor_perf_s) <= frame_window_s
        ]
        detected_window_rows = [row for row in window_rows if int(row["detected"]) == 1]
        matched_row = None
        if detected_window_rows:
            matched_row = min(
                detected_window_rows,
                key=lambda row: abs(float(row["perf_counter_s"]) - anchor_perf_s),
            )
        elif nearest_row is not None:
            matched_row = nearest_row

        nearest_dt_ms = None
        matched_dt_ms = None
        if nearest_row is not None:
            nearest_dt_ms = (float(nearest_row["perf_counter_s"]) - anchor_perf_s) * 1000.0
        if matched_row is not None:
            matched_dt_ms = (float(matched_row["perf_counter_s"]) - anchor_perf_s) * 1000.0

        coincidence_rows.append(
            {
                "pulse_index": int(pulse["pulse_index"]),
                "op598_anchor_ms": anchor_ms,
                "op598_start_ms": float(pulse["start_ms"]),
                "op598_end_ms": float(pulse["end_ms"]),
                "op598_peak_adc": int(pulse["peak_adc"]),
                "op598_threshold_adc": float(pulse["threshold_adc"]),
                "anchor_perf_counter_s": anchor_perf_s,
                "nearest_frame_index": -1 if nearest_row is None else int(nearest_row["frame_index"]),
                "nearest_frame_dt_ms": nearest_dt_ms,
                "matched_frame_index": -1 if matched_row is None else int(matched_row["frame_index"]),
                "matched_frame_dt_ms": matched_dt_ms,
                "window_frame_count": len(window_rows),
                "detected_frame_count": len(detected_window_rows),
                "detected_in_window": bool(detected_window_rows),
                "matched_frame_detected": False if matched_row is None else bool(int(matched_row["detected"])),
                "matched_frame_max": None if matched_row is None else float(matched_row["max"]),
                "matched_frame_p99": None if matched_row is None else float(matched_row["p99"]),
                "matched_frame_threshold": None if matched_row is None else float(matched_row["threshold"]),
            }
        )
    return coincidence_rows


def write_table(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_video_frames(video_path: Path, indexes: list[int]) -> dict[int, np.ndarray]:
    if not video_path.exists() or not indexes:
        return {}
    capture = cv2.VideoCapture(str(video_path))
    try:
        frames: dict[int, np.ndarray] = {}
        for index in sorted(set(indexes)):
            if index < 0:
                continue
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = capture.read()
            if ok:
                frames[index] = frame
        return frames
    finally:
        capture.release()


def save_visual_artifacts(
    paths: dict[str, Path],
    coincidence_rows: list[dict[str, float | int | str | bool | None]],
) -> dict[str, str | int | bool]:
    matched_indexes = [int(row["matched_frame_index"]) for row in coincidence_rows if int(row["matched_frame_index"]) >= 0]
    strip_indexes: list[int] = []
    for index in matched_indexes[: min(6, len(matched_indexes))]:
        strip_indexes.extend([max(0, index - 1), index, index + 1])
    frames = load_video_frames(paths["webcam_video"], matched_indexes + strip_indexes)

    representative_count = 0
    average_inputs: list[np.ndarray] = []
    for row in coincidence_rows:
        frame_index = int(row["matched_frame_index"])
        frame = frames.get(frame_index)
        if frame is None:
            continue
        pulse_index = int(row["pulse_index"])
        output_name = f"pulse_{pulse_index:02d}_frame_{frame_index:06d}.png"
        cv2.imwrite(str(paths["visuals_dir"] / output_name), frame)
        representative_count += 1
        average_inputs.append(frame.astype(np.float32))

    strip_tiles: list[np.ndarray] = []
    for frame_index in matched_indexes[: min(4, len(matched_indexes))]:
        for neighbor in (max(0, frame_index - 1), frame_index, frame_index + 1):
            frame = frames.get(neighbor)
            if frame is not None:
                strip_tiles.append(frame)
    pulse_strip_written = False
    if strip_tiles:
        tile_height = min(frame.shape[0] for frame in strip_tiles)
        resized = [cv2.resize(tile, (tile.shape[1], tile_height)) for tile in strip_tiles]
        cv2.imwrite(str(paths["pulse_strip"]), np.concatenate(resized, axis=1))
        pulse_strip_written = True

    average_written = False
    heatmap_written = False
    if average_inputs:
        average_frame = np.mean(np.stack(average_inputs, axis=0), axis=0).astype(np.uint8)
        cv2.imwrite(str(paths["average_frame"]), average_frame)
        average_written = True

        gray = cv2.cvtColor(average_frame, cv2.COLOR_BGR2GRAY)
        normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(normalized.astype(np.uint8), cv2.COLORMAP_JET)
        cv2.imwrite(str(paths["heatmap"]), heatmap)
        heatmap_written = True

    return {
        "representative_frames": representative_count,
        "average_frame_written": average_written,
        "heatmap_written": heatmap_written,
        "pulse_strip_written": pulse_strip_written,
    }


def write_manifest(
    paths: dict[str, Path],
    args: argparse.Namespace,
    webcam_summary: dict[str, float | int],
    op598_summary: dict[str, str],
    pulse_events: list[dict[str, float | int | str | bool | None]],
    coincidence_rows: list[dict[str, float | int | str | bool | None]],
    visuals_status: dict[str, str | int | bool],
) -> None:
    manifest = {
        "run_id": paths["run_dir"].name,
        "mode": args.mode,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "arguments": vars(args),
        "artifacts": {
            key: display_path(value)
            for key, value in paths.items()
        },
        "webcam_summary": webcam_summary,
        "op598_summary": op598_summary,
        "pulse_count": len(pulse_events),
        "coincidence_pulse_count": len(coincidence_rows),
        "visuals": visuals_status,
    }
    paths["manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_dual_summary(
    paths: dict[str, Path],
    args: argparse.Namespace,
    webcam: dict[str, float | int],
    op598: dict[str, str],
    pulse_events: list[dict[str, float | int | str | bool | None]],
    coincidence_rows: list[dict[str, float | int | str | bool | None]],
    visuals_status: dict[str, str | int | bool],
) -> None:
    detected_windows = sum(1 for row in coincidence_rows if bool(row["detected_in_window"]))
    matched_detected = sum(1 for row in coincidence_rows if bool(row["matched_frame_detected"]))
    frame_offsets = [
        float(row["matched_frame_dt_ms"])
        for row in coincidence_rows
        if row["matched_frame_dt_ms"] is not None
    ]
    mean_offset_ms = float(np.mean(frame_offsets)) if frame_offsets else None
    abs_mean_offset_ms = float(np.mean(np.abs(frame_offsets))) if frame_offsets else None

    with paths["summary_csv"].open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["field", "value"])
        writer.writerow(["mode", args.mode])
        writer.writerow(["webcam.frames", webcam.get("frames", 0)])
        writer.writerow(["webcam.detected_frames", webcam.get("detected_frames", 0)])
        writer.writerow(["webcam.detection_events", webcam.get("detection_events", 0)])
        writer.writerow(["webcam.measured_fps", webcam.get("measured_fps", 0.0)])
        writer.writerow(["op598.pulse_events", len(pulse_events)])
        writer.writerow(["coincidence.detected_windows", detected_windows])
        writer.writerow(["coincidence.matched_detected", matched_detected])
        writer.writerow(["coincidence.mean_offset_ms", mean_offset_ms])
        writer.writerow(["coincidence.abs_mean_offset_ms", abs_mean_offset_ms])
        writer.writerow(["visuals.representative_frames", visuals_status["representative_frames"]])
        writer.writerow(["visuals.average_frame_written", visuals_status["average_frame_written"]])
        writer.writerow(["visuals.heatmap_written", visuals_status["heatmap_written"]])
        writer.writerow(["visuals.pulse_strip_written", visuals_status["pulse_strip_written"]])
        for key, value in sorted(op598.items()):
            writer.writerow([f"op598.{key}", value])

    lines = [
        "# Resumen experimento dual",
        "",
        "## Idea del metodo",
        "",
        "- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.",
        "- OP598 en ADC36 actua como ancla temporal aproximada.",
        "- La webcam aporta coincidencia visual por frame y artefactos para presentacion.",
        "",
        "## Run",
        "",
        f"- Run ID: `{paths['run_dir'].name}`",
        f"- Modo: `{args.mode}`",
        f"- Manifest: `{display_path(paths['manifest'])}`",
        f"- Webcam CSV: `{display_path(paths['webcam_csv'])}`",
        f"- Webcam video: `{display_path(paths['webcam_video'])}`",
        f"- OP598 dir: `{display_path(paths['op598_dir'])}`",
        f"- Pulse events: `{display_path(paths['pulse_events_csv'])}`",
        f"- Coincidencias: `{display_path(paths['coincidence_csv'])}`",
        "",
        "## Webcam",
        "",
        f"- frames: {webcam.get('frames', 0)}",
        f"- detected_frames: {webcam.get('detected_frames', 0)}",
        f"- detection_events: {webcam.get('detection_events', 0)}",
        f"- measured_fps: {webcam.get('measured_fps', 0.0):.2f}",
        "",
        "## Coincidencia",
        "",
        f"- pulsos OP598: {len(pulse_events)}",
        f"- pulsos con deteccion webcam en ventana: {detected_windows}",
        f"- pulsos cuyo frame emparejado quedo detectado: {matched_detected}",
        f"- offset medio frame-ancla (ms): {mean_offset_ms}",
        f"- offset absoluto medio (ms): {abs_mean_offset_ms}",
        f"- ventana usada: {args.coincidence_window_ms} ms",
        "",
        "## Artefactos visuales",
        "",
        f"- representative_frames: {visuals_status['representative_frames']}",
        f"- average_frame_written: {visuals_status['average_frame_written']}",
        f"- heatmap_written: {visuals_status['heatmap_written']}",
        f"- pulse_strip_written: {visuals_status['pulse_strip_written']}",
        "",
        "## Limites actuales",
        "",
        "- El timing del OP598 bajo MicroPython sigue limitado por una cadencia real de ~6.4-6.6 ms.",
        "- La alineacion final sigue siendo por coincidencia estadistica entre un ancla numerica y frames de ~30 FPS.",
        "- Si el OP598 ve un pulso y la webcam no, eso describe sensibilidad distinta entre canales; no invalida el metodo.",
        "",
        "## OP598",
        "",
    ]
    for key, value in sorted(op598.items()):
        lines.append(f"- {key}: {value}")
    paths["summary_md"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_run(
    paths: dict[str, Path], args: argparse.Namespace
) -> tuple[
    dict[str, float | int],
    dict[str, str],
    list[dict[str, float | int | str | bool | None]],
    list[dict[str, float | int | str | bool | None]],
    dict[str, str | int | bool],
]:
    webcam_rows = read_webcam_rows(paths["webcam_csv"])
    webcam_summary = read_webcam_summary(paths["webcam_csv"])
    op598_files = latest_op598_files(paths["op598_dir"])
    op598_summary = read_key_value_summary(op598_files["summary_csv"])
    op598_rows = read_op598_rows(op598_files["csv"])
    pulse_events = build_pulse_events(op598_rows, args.op598_threshold_fraction)
    coincidence_rows = build_coincidence_rows(args, webcam_rows, pulse_events, op598_summary)
    write_table(paths["pulse_events_csv"], pulse_events)
    write_table(paths["coincidence_csv"], coincidence_rows)
    visuals_status = save_visual_artifacts(paths, coincidence_rows)
    return webcam_summary, op598_summary, pulse_events, coincidence_rows, visuals_status


def run(args: argparse.Namespace) -> int:
    paths = build_output_paths(Path(args.output_dir), args.mode)
    detector = run_subprocess(detector_command(args, paths))
    try:
        time.sleep(args.warmup + args.calibration + args.trigger_delay)
        op598_exit = subprocess.run(op598_command(args, paths), check=False).returncode
        detector_exit = detector.wait()
    finally:
        if detector.poll() is None:
            detector.terminate()

    webcam_summary, op598_summary, pulse_events, coincidence_rows, visuals_status = analyze_run(paths, args)
    write_dual_summary(
        paths,
        args,
        webcam_summary,
        op598_summary,
        pulse_events,
        coincidence_rows,
        visuals_status,
    )
    write_manifest(
        paths,
        args,
        webcam_summary,
        op598_summary,
        pulse_events,
        coincidence_rows,
        visuals_status,
    )

    print(f"Run directory: {paths['run_dir']}")
    print(f"Manifest: {paths['manifest']}")
    print(f"Pulse events CSV: {paths['pulse_events_csv']}")
    print(f"Coincidence CSV: {paths['coincidence_csv']}")
    print(f"Dual summary CSV: {paths['summary_csv']}")
    print(f"Dual summary MD: {paths['summary_md']}")
    return 0 if detector_exit == 0 and op598_exit == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a dual OP598 plus webcam flash experiment from one command."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_ROOT), help="Root directory for each run")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="ESP32 serial port")
    parser.add_argument("--baud", type=int, default=115200, help="ESP32 serial baudrate")

    parser.add_argument("--index", type=int, default=2, help="OpenCV camera index")
    parser.add_argument("--width", type=int, default=640, help="Camera width")
    parser.add_argument("--height", type=int, default=480, help="Camera height")
    parser.add_argument("--fps", type=int, default=30, help="Camera FPS")
    parser.add_argument("--fourcc", default="YUYV", help="Camera FOURCC")
    parser.add_argument("--raw", action="store_true", help="Use raw webcam mode")
    parser.add_argument("--preview", action="store_true", help="Show webcam preview")
    parser.add_argument("--save-detected-frames", action="store_true", help="Save representative webcam frames")
    parser.add_argument("--roi", help="Manual webcam ROI x,y,w,h")
    parser.add_argument("--auto-exposure", choices=("auto", "manual"))
    parser.add_argument("--exposure", type=float)
    parser.add_argument("--exposure-auto-priority", type=int, choices=(0, 1))
    parser.add_argument("--metric", choices=("mean", "max", "p99"), default="max")
    parser.add_argument("--threshold-delta", type=float, default=30.0)
    parser.add_argument("--sigma-multiplier", type=float, default=1.0)
    parser.add_argument("--warmup", type=float, default=1.0)
    parser.add_argument("--calibration", type=float, default=3.0)
    parser.add_argument("--trigger-delay", type=float, default=1.0)
    parser.add_argument("--tail-seconds", type=float, default=2.0, help="Extra webcam tail after the profile")
    parser.add_argument(
        "--coincidence-window-ms",
        type=float,
        default=100.0,
        help="Window around each OP598 anchor used to search webcam coincidences",
    )

    parser.add_argument("--live-sensor-plot", action="store_true", help="Show live OP598 plot if a GUI display is available")
    parser.add_argument("--op598-print-every", type=int, default=50, help="Print OP598 status every N samples")
    parser.add_argument("--op598-threshold-fraction", type=float, default=0.5)
    parser.add_argument("--op598-verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    pulse_parser = subparsers.add_parser("pulse", help="Run a single pulse dual experiment")
    pulse_parser.add_argument("--duration-ms", type=int, default=40)
    pulse_parser.add_argument("--duty", type=int, default=1023)
    pulse_parser.add_argument("--pre-ms", type=int, default=40)
    pulse_parser.add_argument("--post-ms", type=int, default=120)
    pulse_parser.add_argument("--sample-us", type=int, default=1000)

    train_parser = subparsers.add_parser("train", help="Run a fixed-period dual train experiment")
    train_parser.add_argument("--count", type=int, default=5)
    train_parser.add_argument("--period-ms", type=int, default=1000)
    train_parser.add_argument("--duration-ms", type=int, default=40)
    train_parser.add_argument("--duty", type=int, default=1023)
    train_parser.add_argument("--pre-ms", type=int, default=40)
    train_parser.add_argument("--post-ms", type=int, default=120)
    train_parser.add_argument("--sample-us", type=int, default=1000)

    random_parser = subparsers.add_parser("random-train", help="Run a random dark-interval coincidence experiment")
    random_parser.add_argument("--count", type=int, default=30)
    random_parser.add_argument("--min-period-ms", type=int, default=1800)
    random_parser.add_argument("--max-period-ms", type=int, default=2100)
    random_parser.add_argument("--duration-ms", type=int, default=40)
    random_parser.add_argument("--duty", type=int, default=1023)
    random_parser.add_argument("--pre-ms", type=int, default=40)
    random_parser.add_argument("--post-ms", type=int, default=120)
    random_parser.add_argument("--sample-us", type=int, default=1000)

    return parser.parse_args()


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    sys.exit(main())
