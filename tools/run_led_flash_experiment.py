"""
Run a simple webcam + ESP32 LED flash experiment from one terminal.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from led_serial_control import send_command
from run_led_intensity_sweep import duty_percent

try:
    import serial
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit("pyserial is not installed. Run: python -m pip install -r requirements.txt") from exc


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DETECTOR = PROJECT_ROOT / "tools" / "webcam_flash_detector.py"


def run(args: argparse.Namespace) -> int:
    detector_cmd = [
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
    ]
    if args.raw:
        detector_cmd.append("--raw")
    if args.preview:
        detector_cmd.append("--preview")
    if args.save_detected_frames:
        detector_cmd.append("--save-detected-frames")
    if args.frames_dir:
        detector_cmd += ["--frames-dir", args.frames_dir]
    if args.auto_exposure:
        detector_cmd += ["--auto-exposure", args.auto_exposure]
    if args.exposure is not None:
        detector_cmd += ["--exposure", str(args.exposure)]
    if args.exposure_auto_priority is not None:
        detector_cmd += ["--exposure-auto-priority", str(args.exposure_auto_priority)]

    detector = subprocess.Popen(detector_cmd)
    try:
        time.sleep(args.warmup + args.calibration + args.trigger_delay)
        command = f"train {args.count} {args.period_ms} {args.duration_ms} {args.duty}"
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
            output = send_command(serial_port, command, train_wait)
        print(f"> {command}")
        print(f"Intensity: duty {args.duty}/1023 ({duty_percent(args.duty):.2f}%)")
        print(output.rstrip() if output.strip() else "No response received.")
        return detector.wait()
    finally:
        if detector.poll() is None:
            detector.terminate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coordinate webcam flash detection with an ESP32 LED pulse train."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0", help="ESP32 serial port")
    parser.add_argument("--baud", type=int, default=115200, help="ESP32 baudrate")
    parser.add_argument("--read-wait", type=float, default=1.0, help="Seconds to wait for ACK")
    parser.add_argument("--count", type=int, default=5, help="Pulse count")
    parser.add_argument("--period-ms", type=int, default=1000, help="Pulse period")
    parser.add_argument("--duration-ms", type=int, default=100, help="Pulse duration")
    parser.add_argument("--duty", type=int, default=1023, help="Pulse PWM intensity duty 0-1023; percent = duty / 1023 * 100")
    parser.add_argument("--trigger-delay", type=float, default=1.0, help="Delay after baseline before train")
    parser.add_argument("--index", type=int, default=2, help="OpenCV camera index")
    parser.add_argument("--width", type=int, default=640, help="Camera width")
    parser.add_argument("--height", type=int, default=480, help="Camera height")
    parser.add_argument("--fps", type=int, default=30, help="Camera FPS")
    parser.add_argument("--fourcc", default="YUYV", help="Camera FOURCC")
    parser.add_argument("--raw", action="store_true", help="Disable OpenCV RGB conversion")
    parser.add_argument("--preview", action="store_true", help="Show detector preview")
    parser.add_argument("--save-detected-frames", action="store_true", help="Save PNG frames detected as flashes")
    parser.add_argument("--frames-dir", default="data/webcam/flash_presentation/demo", help="Directory for detected PNG frames")
    parser.add_argument("--seconds", type=float, default=12.0, help="Detector run seconds")
    parser.add_argument("--warmup", type=float, default=1.0, help="Detector warmup seconds")
    parser.add_argument("--calibration", type=float, default=3.0, help="Dark calibration seconds")
    parser.add_argument(
        "--metric",
        choices=("mean", "max", "p99"),
        default="max",
        help="Detection metric. max is best for a small point LED",
    )
    parser.add_argument(
        "--threshold-delta",
        type=float,
        default=30.0,
        help="Absolute threshold above dark baseline",
    )
    parser.add_argument("--auto-exposure", choices=("auto", "manual"))
    parser.add_argument("--exposure", type=float)
    parser.add_argument("--exposure-auto-priority", type=int, choices=(0, 1))
    return parser.parse_args()


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    sys.exit(main())
