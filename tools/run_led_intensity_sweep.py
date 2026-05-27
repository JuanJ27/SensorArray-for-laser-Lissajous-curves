"""
Find the minimum LED PWM duty detectable by the webcam flash detector.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.aggregate import (
    CAMERA0_THRESHOLD_CAMPAIGN_ID,
    FIXED_PULSES_PER_DUTY,
    REQUIRED_CAMERA0_DUTIES,
    generate_camera0_threshold_artifacts,
)
try:
    from led_serial_control import send_command
except ModuleNotFoundError:  # pragma: no cover - package import path for tests
    from tools.led_serial_control import send_command
DETECTOR = PROJECT_ROOT / "tools" / "webcam_flash_detector.py"
SUMMARY_PATTERNS = {
    "detected_frames": re.compile(r"Detected frames:\s+(\d+)"),
    "detection_events": re.compile(r"Detection events:\s+(\d+)"),
    "measured_fps": re.compile(r"Measured FPS:\s+([0-9.]+)"),
    "csv": re.compile(r"CSV:\s+(.+)"),
    "frames_dir": re.compile(r"Detected frames directory:\s+(.+)"),
}


def parse_duties(value: str) -> list[int]:
    duties = [int(item.strip()) for item in value.split(",") if item.strip()]
    return [max(0, min(1023, duty)) for duty in duties]


def default_output_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"led_intensity_sweep_{timestamp}.csv"


def duty_percent(duty: int) -> float:
    return duty / 1023 * 100


def detector_command(args: argparse.Namespace) -> list[str]:
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
        str(args.seconds),
        "--warmup",
        str(args.warmup),
        "--calibration",
        str(args.calibration),
        "--metric",
        args.metric,
        "--threshold-delta",
        str(args.threshold_delta),
        "--status-interval",
        str(args.status_interval),
    ]
    if args.raw:
        command.append("--raw")
    if args.preview:
        command.append("--preview")
    if args.save_detected_frames:
        command.append("--save-detected-frames")
    if args.frames_dir:
        command += ["--frames-dir", str(Path(args.frames_dir) / f"duty_{args.current_duty:04d}")]
    if args.auto_exposure:
        command += ["--auto-exposure", args.auto_exposure]
    if args.exposure is not None:
        command += ["--exposure", str(args.exposure)]
    if args.exposure_auto_priority is not None:
        command += ["--exposure-auto-priority", str(args.exposure_auto_priority)]
    return command


def parse_detector_output(output: str) -> dict[str, str | int | float]:
    parsed: dict[str, str | int | float] = {}
    for key, pattern in SUMMARY_PATTERNS.items():
        match = pattern.search(output)
        if not match:
            continue
        value = match.group(1).strip()
        if key in {"detected_frames", "detection_events"}:
            parsed[key] = int(value)
        elif key == "measured_fps":
            parsed[key] = float(value)
        else:
            parsed[key] = value
    return parsed


def send_train(args: argparse.Namespace, duty: int) -> str:
    try:
        import serial
    except ImportError as exc:  # pragma: no cover - exercised only without dependency
        raise SystemExit("pyserial is not installed. Run: python -m pip install -r requirements.txt") from exc
    command = f"train {args.count} {args.period_ms} {args.duration_ms} {duty}"
    train_wait = max(
        args.read_wait,
        (max(0, args.count - 1) * args.period_ms + args.duration_ms) / 1000.0 + 1.0,
    )
    with serial.Serial(args.port, args.baud, timeout=1.0) as serial_port:
        serial_port.dtr = True
        serial_port.rts = False
        time.sleep(1.0)
        serial_port.reset_input_buffer()
        send_command(serial_port, "boardled off", args.read_wait)
        send_command(serial_port, "off", args.read_wait)
        return send_command(serial_port, command, train_wait)


def run_one(args: argparse.Namespace, duty: int) -> dict[str, str | int | float]:
    detector = subprocess.Popen(
        detector_command(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    try:
        time.sleep(args.warmup + args.calibration + args.trigger_delay)
        led_output = send_train(args, duty)
        print(f"duty={duty} led_ack={led_output.strip() or 'no response'}")
        output, _ = detector.communicate(timeout=args.seconds + args.warmup + args.calibration + 5)
        lines.append(output)
    finally:
        if detector.poll() is None:
            detector.terminate()

    detector_output = "".join(lines)
    print(detector_output.rstrip())
    result = parse_detector_output(detector_output)
    result["duty"] = duty
    result["intensity_percent"] = duty_percent(duty)
    result["led_ack"] = led_output.strip()
    return result


def build_camera0_campaign_plan(
    campaign_id: str,
    camera_index: int,
    pulses_per_duty: int = FIXED_PULSES_PER_DUTY,
    seed: int = 7,
) -> list[dict[str, int | str | bool]]:
    duties = sorted(REQUIRED_CAMERA0_DUTIES)
    pulse_counts = {duty: 0 for duty in duties}
    rows: list[dict[str, int | str | bool]] = []
    rng = random.Random(seed)
    for block_id in range(1, pulses_per_duty + 1):
        block_duties = duties[:]
        rng.shuffle(block_duties)
        for block_order, duty in enumerate(block_duties, start=1):
            pulse_counts[duty] += 1
            rows.append(
                {
                    "campaign_id": campaign_id,
                    "camera_index": camera_index,
                    "duty": duty,
                    "pulse_index": pulse_counts[duty],
                    "block_id": block_id,
                    "block_order": block_order,
                    "is_dark_control": duty == 0,
                    "is_positive_control": duty in {16, 24, 32, 48, 64, 128},
                }
            )
    return rows


def emit_plan_only(args: argparse.Namespace) -> int:
    if args.run_intent != "threshold":
        raise SystemExit("--emit-plan-only requires --run-intent threshold")
    plan_rows = build_camera0_campaign_plan(
        campaign_id=args.campaign_id,
        camera_index=args.index,
        pulses_per_duty=FIXED_PULSES_PER_DUTY,
        seed=args.plan_seed,
    )
    output_path = Path(args.plan_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(plan_rows[0].keys()) if plan_rows else []
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(plan_rows)

    metadata = {
        "campaign_id": args.campaign_id,
        "run_intent": args.run_intent,
        "camera_index": args.index,
        "plan_rows": len(plan_rows),
        "duties": sorted(REQUIRED_CAMERA0_DUTIES),
        "pulses_per_duty": FIXED_PULSES_PER_DUTY,
        "plan_output": str(output_path),
    }
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


def emit_offline_artifacts(args: argparse.Namespace) -> int:
    input_path = Path(args.offline_input_csv)
    if not input_path.exists():
        raise SystemExit(f"offline input CSV not found: {input_path}")
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = generate_camera0_threshold_artifacts(
        input_rows=rows,
        studies_dir=Path(args.studies_dir),
        campaign_id=args.campaign_id,
        camera_index=args.index,
    )
    result["run_intent"] = args.run_intent
    result["camera_index"] = args.index
    result["campaign_id"] = args.campaign_id
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run(args: argparse.Namespace) -> int:
    if args.emit_plan_only:
        return emit_plan_only(args)
    if args.emit_offline_artifacts:
        return emit_offline_artifacts(args)
    if args.run_intent == "threshold" and args.index != 0:
        raise SystemExit("threshold run_intent requires --index 0")

    duties = parse_duties(args.duties)
    output_path = Path(args.output) if args.output else default_output_path(Path(args.output_dir))
    rows = []

    for duty in duties:
        print(f"\n=== Testing duty {duty}/1023 ({duty_percent(duty):.2f}%) ===")
        args.current_duty = duty
        rows.append(run_one(args, duty))
        time.sleep(args.between_tests)

    fieldnames = [
        "duty",
        "intensity_percent",
        "detection_events",
        "detected_frames",
        "measured_fps",
        "csv",
        "frames_dir",
        "led_ack",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    detected = [row for row in rows if int(row.get("detection_events", 0)) > 0]
    minimum = min((int(row["duty"]) for row in detected), default=None)
    print("\nSweep summary:")
    print(f"  Output: {output_path}")
    if minimum is None:
        print("  Minimum detected intensity: none")
    else:
        print(f"  Minimum detected intensity: duty {minimum}/1023 ({duty_percent(minimum):.2f}%)")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep LED PWM duty and detect flashes with the webcam. "
            "Duty is the PWM intensity scale 0-1023; percent = duty / 1023 * 100."
        )
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--read-wait", type=float, default=1.0)
    parser.add_argument(
        "--duties",
        default="32,64,96,128,192,256,384,512,768,1023",
        help="Comma-separated PWM intensities in duty units 0-1023; percent = duty / 1023 * 100",
    )
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--period-ms", type=int, default=700)
    parser.add_argument("--duration-ms", type=int, default=200)
    parser.add_argument("--trigger-delay", type=float, default=0.7)
    parser.add_argument("--between-tests", type=float, default=0.5)
    parser.add_argument("--index", type=int, default=2)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--run-intent", choices=("threshold", "tuning"), required=True)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--fourcc", default="YUYV")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--preview", action="store_true", help="Show live camera preview during each detector run")
    parser.add_argument("--seconds", type=float, default=7.0)
    parser.add_argument("--warmup", type=float, default=0.5)
    parser.add_argument("--calibration", type=float, default=2.0)
    parser.add_argument("--metric", choices=("mean", "max", "p99"), default="max")
    parser.add_argument("--threshold-delta", type=float, default=30.0)
    parser.add_argument("--status-interval", type=float, default=2.0)
    parser.add_argument("--auto-exposure", choices=("auto", "manual"), default="manual")
    parser.add_argument("--exposure", type=float, default=10)
    parser.add_argument("--exposure-auto-priority", type=int, choices=(0, 1), default=0)
    parser.add_argument("--output")
    parser.add_argument("--output-dir", default="data/webcam")
    parser.add_argument("--save-detected-frames", action="store_true", help="Save PNG frames detected as flashes")
    parser.add_argument("--frames-dir", default="data/webcam/flash_presentation/intensity", help="Base directory for detected PNG frames")
    parser.add_argument("--emit-plan-only", action="store_true", help="Only emit offline campaign plan CSV; do not run hardware")
    parser.add_argument("--plan-seed", type=int, default=7)
    parser.add_argument(
        "--plan-output",
        default="data/derived/studies/camera0_intensity_campaign_plan.csv",
        help="CSV output path for --emit-plan-only mode",
    )
    parser.add_argument("--emit-offline-artifacts", action="store_true", help="Generate camera0 artifacts from offline fixture CSV")
    parser.add_argument("--offline-input-csv", default="data/derived/studies/camera0_fixture_input.csv")
    parser.add_argument("--studies-dir", default="data/derived/studies")
    return parser.parse_args()


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    sys.exit(main())
