"""
Run practical webcam flash detectability sweeps with the ESP32 LED controller.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from run_led_intensity_sweep import duty_percent, parse_detector_output, send_train


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DETECTOR = PROJECT_ROOT / "tools" / "webcam_flash_detector.py"


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def default_output_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"flash_parameter_sweep_{timestamp}.csv"


def detector_command(args: argparse.Namespace, exposure: float, frames_suffix: str) -> list[str]:
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
        "--auto-exposure",
        "manual",
        "--exposure",
        str(exposure),
        "--exposure-auto-priority",
        str(args.exposure_auto_priority),
    ]
    if args.raw:
        command.append("--raw")
    if args.preview:
        command.append("--preview")
    if args.save_detected_frames:
        command.append("--save-detected-frames")
    if args.frames_dir:
        command += ["--frames-dir", str(Path(args.frames_dir) / frames_suffix)]
    return command


def run_trial(
    args: argparse.Namespace,
    sweep: str,
    value: int | float,
    exposure: float,
    duration_ms: int,
) -> dict[str, str | int | float]:
    detector = subprocess.Popen(
        detector_command(args, exposure, f"{sweep}_{str(value).replace('.', '_')}"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        time.sleep(args.warmup + args.calibration + args.trigger_delay)
        trial_args = argparse.Namespace(**vars(args))
        trial_args.duration_ms = duration_ms
        led_output = send_train(trial_args, args.duty)
        print(f"{sweep}={value} led_ack={led_output.strip() or 'no response'}")
        output, _ = detector.communicate(timeout=args.seconds + args.warmup + args.calibration + 5)
    finally:
        if detector.poll() is None:
            detector.terminate()

    print(output.rstrip())
    result = parse_detector_output(output)
    result.update(
        {
            "sweep": sweep,
            "value": value,
            "duty": args.duty,
            "intensity_percent": duty_percent(args.duty),
            "duration_ms": duration_ms,
            "exposure": exposure,
            "led_ack": led_output.strip(),
        }
    )
    return result


def run(args: argparse.Namespace) -> int:
    output_path = Path(args.output) if args.output else default_output_path(Path(args.output_dir))
    rows: list[dict[str, str | int | float]] = []

    for exposure in parse_float_list(args.exposures):
        print(f"\n=== Exposure sweep exposure={exposure} ===")
        rows.append(run_trial(args, "exposure", exposure, exposure, args.duration_ms))
        time.sleep(args.between_tests)

    for duration_ms in parse_int_list(args.durations_ms):
        print(f"\n=== Duration sweep duration_ms={duration_ms} ===")
        rows.append(run_trial(args, "duration_ms", duration_ms, args.exposure, duration_ms))
        time.sleep(args.between_tests)

    fieldnames = [
        "sweep",
        "value",
        "duty",
        "intensity_percent",
        "duration_ms",
        "exposure",
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

    print("\nParameter sweep summary:")
    print(f"  Output: {output_path}")
    print(f"  LED intensity: duty {args.duty}/1023 ({duty_percent(args.duty):.2f}%)")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep webcam exposure and pulse duration for LED flash detectability. "
            "Duty is the PWM intensity scale 0-1023; percent = duty / 1023 * 100."
        )
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--read-wait", type=float, default=1.0)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--period-ms", type=int, default=700)
    parser.add_argument("--duration-ms", type=int, default=100)
    parser.add_argument("--duty", type=int, default=128, help="Pulse PWM intensity duty 0-1023; percent = duty / 1023 * 100")
    parser.add_argument("--trigger-delay", type=float, default=0.7)
    parser.add_argument("--between-tests", type=float, default=0.5)
    parser.add_argument("--index", type=int, default=2)
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
    parser.add_argument("--exposure", type=float, default=10)
    parser.add_argument("--exposures", default="3,5,10,20,40")
    parser.add_argument("--durations-ms", default="10,20,50,100,200,300")
    parser.add_argument("--exposure-auto-priority", type=int, choices=(0, 1), default=0)
    parser.add_argument("--output")
    parser.add_argument("--output-dir", default="data/webcam")
    parser.add_argument("--save-detected-frames", action="store_true", help="Save PNG frames detected as flashes")
    parser.add_argument("--frames-dir", default="data/webcam/flash_presentation/parameters", help="Base directory for detected PNG frames")
    return parser.parse_args()


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    sys.exit(main())
