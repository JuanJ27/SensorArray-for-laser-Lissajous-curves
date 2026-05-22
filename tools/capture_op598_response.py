"""
Capture OP598 response profiles from the ESP32 firmware and save analysis artifacts.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    import matplotlib

    if not os.environ.get("DISPLAY"):
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit(
        "matplotlib is not installed. Run: python -m pip install -r requirements.txt"
    ) from exc

try:
    import serial
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit("pyserial is not installed. Run: python -m pip install -r requirements.txt") from exc


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "op598"
CSV_FIELDS = (
    "index",
    "t_us",
    "t_ms",
    "adc",
    "led",
    "phase",
    "pulse_index",
)


def parse_key_values(line: str) -> dict[str, str]:
    parts = line.strip().split()
    values: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key] = value
    return values


def build_paths(output_dir: Path, label: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{label}_{timestamp}"
    return {
        "csv": output_dir / f"{stem}.csv",
        "summary_csv": output_dir / f"{stem}_summary.csv",
        "summary_md": output_dir / f"{stem}_summary.md",
        "plot": output_dir / f"{stem}.png",
        "log": output_dir / f"{stem}.log",
    }


def open_serial_port(args: argparse.Namespace) -> serial.Serial:
    serial_port = serial.Serial(args.port, args.baud, timeout=args.timeout)
    serial_port.dtr = args.dtr
    serial_port.rts = args.rts
    time.sleep(args.startup_wait)
    if args.soft_reboot:
        serial_port.write(b"\x03")
        serial_port.flush()
        time.sleep(0.2)
        serial_port.write(b"\x04")
        serial_port.flush()
        time.sleep(args.reboot_wait)
    if args.reset_input:
        serial_port.reset_input_buffer()
    return serial_port


def send_line(serial_port: serial.Serial, command: str) -> None:
    serial_port.write((command.strip() + "\n").encode("utf-8"))
    serial_port.flush()


def live_plot_enabled(args: argparse.Namespace) -> bool:
    return args.live_plot and matplotlib.get_backend().lower() != "agg"


def make_live_plot(title: str):
    plt.ion()
    figure, axis = plt.subplots(figsize=(10, 4))
    sensor_line, = axis.plot([], [], color="tab:green", label="ADC36 OP598")
    led_line, = axis.plot([], [], color="tab:red", alpha=0.5, label="LED state x adc max")
    axis.set_title(title)
    axis.set_xlabel("Time (ms)")
    axis.set_ylabel("ADC")
    axis.grid(True, alpha=0.3)
    axis.legend(loc="upper right")
    return figure, axis, sensor_line, led_line


def update_live_plot(axis, sensor_line, led_line, rows: list[dict[str, float | int | str]]) -> None:
    if not rows:
        return
    x_values = [float(row["t_ms"]) for row in rows]
    adc_values = [float(row["adc"]) for row in rows]
    max_adc = max(adc_values) if adc_values else 1.0
    led_values = [float(row["led"]) * max_adc for row in rows]
    sensor_line.set_data(x_values, adc_values)
    led_line.set_data(x_values, led_values)
    axis.relim()
    axis.autoscale_view()
    axis.figure.canvas.draw()
    axis.figure.canvas.flush_events()


def final_plot(rows: list[dict[str, float | int | str]], metrics: dict[str, float | str | int | None], plot_path: Path, title: str) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    times_ms = np.array([float(row["t_ms"]) for row in rows], dtype=float)
    adc_values = np.array([float(row["adc"]) for row in rows], dtype=float)
    led_values = np.array([float(row["led"]) for row in rows], dtype=float)
    axis.plot(times_ms, adc_values, color="tab:green", linewidth=1.4, label="OP598 ADC36")
    if len(adc_values):
        axis.plot(times_ms, led_values * float(np.max(adc_values)), color="tab:red", alpha=0.35, label="LED state")
    threshold = metrics.get("threshold_adc")
    if threshold is not None and not math.isnan(float(threshold)):
        axis.axhline(float(threshold), color="tab:orange", linestyle="--", label="Threshold")
    crossing_ms = metrics.get("threshold_crossing_ms")
    if crossing_ms is not None and not math.isnan(float(crossing_ms)):
        axis.axvline(float(crossing_ms), color="tab:purple", linestyle=":", label="Threshold crossing")
    axis.set_title(title)
    axis.set_xlabel("Time (ms)")
    axis.set_ylabel("ADC count")
    axis.grid(True, alpha=0.3)
    axis.legend(loc="best")
    figure.tight_layout()
    figure.savefig(plot_path, dpi=160)
    plt.close(figure)


def first_crossing_time(times_ms: np.ndarray, values: np.ndarray, threshold: float, start_index: int = 0, rising: bool = True) -> float | None:
    comparator = np.greater_equal if rising else np.less_equal
    for index in range(max(0, start_index), len(values)):
        if comparator(values[index], threshold):
            return float(times_ms[index])
    return None


def pulse_start_candidates(rows: list[dict[str, float | int | str]]) -> list[float]:
    starts: list[float] = []
    previous_led = 0
    for row in rows:
        current_led = int(row["led"])
        if current_led == 1 and previous_led == 0:
            starts.append(float(row["t_ms"]))
        previous_led = current_led
    return starts


def compute_metrics(rows: list[dict[str, float | int | str]], threshold_fraction: float) -> dict[str, float | int | str | None]:
    if not rows:
        return {
            "sample_count": 0,
            "baseline_adc": None,
            "peak_adc": None,
            "threshold_adc": None,
            "threshold_crossing_ms": None,
            "rise_time_ms": None,
            "fall_time_ms": None,
            "pulse_width_ms": None,
            "peak_time_ms": None,
            "pulse_count": 0,
        }

    times_ms = np.array([float(row["t_ms"]) for row in rows], dtype=float)
    adc_values = np.array([float(row["adc"]) for row in rows], dtype=float)
    phases = [str(row["phase"]) for row in rows]
    pulse_count = len(pulse_start_candidates(rows))

    baseline_values = adc_values[[phase == "pre" for phase in phases]]
    if not len(baseline_values):
        baseline_values = adc_values[: max(1, len(adc_values) // 10)]
    baseline_adc = float(np.mean(baseline_values))
    peak_index = int(np.argmax(adc_values))
    peak_adc = float(adc_values[peak_index])
    peak_time_ms = float(times_ms[peak_index])
    amplitude = max(0.0, peak_adc - baseline_adc)
    threshold_adc = baseline_adc + amplitude * threshold_fraction
    sample_intervals = np.diff(times_ms) if len(times_ms) > 1 else np.array([], dtype=float)

    if amplitude <= 0.0:
        return {
            "sample_count": int(len(rows)),
            "baseline_adc": baseline_adc,
            "peak_adc": peak_adc,
            "threshold_adc": None,
            "threshold_crossing_ms": None,
            "rise_time_ms": None,
            "fall_time_ms": None,
            "pulse_width_ms": None,
            "peak_time_ms": peak_time_ms,
            "pulse_count": pulse_count,
            "sample_interval_avg_ms": None if not len(sample_intervals) else float(np.mean(sample_intervals)),
            "sample_interval_min_ms": None if not len(sample_intervals) else float(np.min(sample_intervals)),
            "sample_interval_max_ms": None if not len(sample_intervals) else float(np.max(sample_intervals)),
        }

    if pulse_count > 1:
        return {
            "sample_count": int(len(rows)),
            "baseline_adc": baseline_adc,
            "peak_adc": peak_adc,
            "threshold_adc": threshold_adc,
            "threshold_crossing_ms": None,
            "rise_time_ms": None,
            "fall_time_ms": None,
            "pulse_width_ms": None,
            "peak_time_ms": peak_time_ms,
            "pulse_count": pulse_count,
            "sample_interval_avg_ms": None if not len(sample_intervals) else float(np.mean(sample_intervals)),
            "sample_interval_min_ms": None if not len(sample_intervals) else float(np.min(sample_intervals)),
            "sample_interval_max_ms": None if not len(sample_intervals) else float(np.max(sample_intervals)),
        }

    threshold_crossing_ms = first_crossing_time(times_ms, adc_values, threshold_adc)
    ten_threshold = baseline_adc + amplitude * 0.1
    ninety_threshold = baseline_adc + amplitude * 0.9
    rise_start = first_crossing_time(times_ms, adc_values, ten_threshold)
    rise_end = first_crossing_time(times_ms, adc_values, ninety_threshold)

    fall_start = None
    fall_end = None
    for index in range(peak_index, len(adc_values)):
        if adc_values[index] <= ninety_threshold:
            fall_start = float(times_ms[index])
            break
    for index in range(peak_index, len(adc_values)):
        if adc_values[index] <= ten_threshold:
            fall_end = float(times_ms[index])
            break

    pulse_width_end = None
    if threshold_crossing_ms is not None:
        after_peak = first_crossing_time(times_ms, adc_values, threshold_adc, start_index=peak_index, rising=False)
        pulse_width_end = after_peak

    return {
        "sample_count": int(len(rows)),
        "baseline_adc": baseline_adc,
        "peak_adc": peak_adc,
        "threshold_adc": threshold_adc,
        "threshold_crossing_ms": threshold_crossing_ms,
        "rise_time_ms": None if rise_start is None or rise_end is None else rise_end - rise_start,
        "fall_time_ms": None if fall_start is None or fall_end is None else fall_end - fall_start,
        "pulse_width_ms": None if threshold_crossing_ms is None or pulse_width_end is None else pulse_width_end - threshold_crossing_ms,
        "peak_time_ms": peak_time_ms,
        "pulse_count": pulse_count,
        "sample_interval_avg_ms": None if not len(sample_intervals) else float(np.mean(sample_intervals)),
        "sample_interval_min_ms": None if not len(sample_intervals) else float(np.min(sample_intervals)),
        "sample_interval_max_ms": None if not len(sample_intervals) else float(np.max(sample_intervals)),
    }


def write_rows(csv_path: Path, rows: list[dict[str, float | int | str]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary_csv: Path, summary_md: Path, command: str, metadata: dict[str, str], metrics: dict[str, float | int | str | None], paths: dict[str, Path]) -> None:
    with summary_csv.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["field", "value"])
        writer.writerow(["command", command])
        for key in sorted(metadata):
            writer.writerow([f"metadata.{key}", metadata[key]])
        for key in sorted(metrics):
            writer.writerow([key, metrics[key]])

    lines = [
        "# Resumen OP598",
        "",
        f"- Comando: `{command}`",
        f"- CSV: `{paths['csv']}`",
        f"- Plot: `{paths['plot']}`",
        "",
        "## Metricas",
        "",
    ]
    for key in sorted(metrics):
        lines.append(f"- {key}: {metrics[key]}")
    lines += ["", "## Metadata", ""]
    for key in sorted(metadata):
        lines.append(f"- {key}: {metadata[key]}")
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_command(args: argparse.Namespace) -> tuple[str, str]:
    if args.mode == "status":
        return "sensor status", "op598_status"
    if args.mode == "sample":
        delay_token = f"{args.sample_delay}{args.sample_unit}"
        return f"sensor sample {args.sample_count} {delay_token}", "op598_sample"
    if args.mode == "pulse":
        command = (
            f"sensor pulse_profile {args.duration_ms} {args.duty} {args.pre_ms} {args.post_ms} {args.sample_us}"
        )
        return command, "op598_pulse_profile"
    if args.mode == "train":
        command = (
            f"sensor train_profile {args.count} {args.period_ms} {args.duration_ms} {args.duty} "
            f"{args.pre_ms} {args.post_ms} {args.sample_us}"
        )
        return command, "op598_train_profile"
    command = (
        f"sensor random_train_profile {args.count} {args.min_period_ms} {args.max_period_ms} {args.duration_ms} {args.duty} "
        f"{args.pre_ms} {args.post_ms} {args.sample_us}"
    )
    return command, "op598_random_train_profile"


def estimated_timeout(args: argparse.Namespace) -> float:
    if args.mode == "status":
        return max(args.read_wait, 1.0)
    if args.mode == "sample":
        multiplier = 0.001 if args.sample_unit == "ms" else 0.000001
        return max(args.read_wait, args.sample_count * args.sample_delay * multiplier + 2.0)
    if args.mode == "pulse":
        total_ms = args.pre_ms + args.duration_ms + args.post_ms
        return max(args.read_wait, total_ms / 1000.0 + 3.0)
    if args.mode == "train":
        total_ms = args.pre_ms + args.post_ms + max(0, args.count - 1) * args.period_ms + args.duration_ms
        return max(args.read_wait, total_ms / 1000.0 + 3.0)
    total_ms = args.pre_ms + args.post_ms + max(0, args.count - 1) * args.max_period_ms + args.duration_ms
    return max(args.read_wait, total_ms / 1000.0 + 3.0)


def capture_lines(serial_port: serial.Serial, command: str, timeout_s: float, args: argparse.Namespace):
    rows: list[dict[str, float | int | str]] = []
    log_lines: list[str] = []
    metadata: dict[str, str] = {}
    final_status = ""
    deadline = time.time() + timeout_s
    figure = axis = sensor_line = led_line = None

    if live_plot_enabled(args):
        figure, axis, sensor_line, led_line = make_live_plot(command)

    metadata["host_command_sent_perf_counter_s"] = f"{time.perf_counter():.9f}"
    metadata["host_command_sent_wall_time_s"] = f"{time.time():.9f}"
    send_line(serial_port, command)
    while time.time() < deadline:
        raw_line = serial_port.readline()
        if not raw_line:
            continue
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        log_lines.append(line)
        if args.verbose:
            print(line)

        if line.startswith("SENSOR_ROW "):
            fields = parse_key_values(line)
            row = {
                "index": int(fields.get("index", 0)),
                "t_us": int(fields.get("t_us", 0)),
                "t_ms": int(fields.get("t_us", 0)) / 1000.0,
                "adc": int(fields.get("adc", 0)),
                "led": int(fields.get("led", 0)),
                "phase": fields.get("phase", "unknown"),
                "pulse_index": int(fields.get("pulse_index", -1)),
            }
            rows.append(row)
            if axis is not None and len(rows) % max(1, args.plot_every) == 0:
                update_live_plot(axis, sensor_line, led_line, rows)
            if args.print_every and len(rows) % args.print_every == 0:
                print(
                    f"samples={len(rows)} t_ms={row['t_ms']:.2f} adc={row['adc']} led={row['led']} phase={row['phase']}"
                )
            deadline = time.time() + max(1.0, args.read_wait)
            continue

        if line.startswith("OK "):
            fields = parse_key_values(line)
            metadata.update(fields)
            final_status = line
            if command.startswith("sensor status") or fields.get("command") == "sensor_status":
                break
            if command.startswith("sensor ") and line.startswith("OK sensor_"):
                break

    if figure is not None:
        plt.close(figure)
    metadata["host_capture_finished_perf_counter_s"] = f"{time.perf_counter():.9f}"
    metadata["host_capture_finished_wall_time_s"] = f"{time.time():.9f}"
    return rows, metadata, log_lines, final_status


def run(args: argparse.Namespace) -> int:
    command, label = build_command(args)
    paths = build_paths(Path(args.output_dir), label)
    with open_serial_port(args) as serial_port:
        rows, metadata, log_lines, final_status = capture_lines(serial_port, command, estimated_timeout(args), args)

    paths["log"].write_text("\n".join(log_lines) + ("\n" if log_lines else ""), encoding="utf-8")

    print(f"> {command}")
    if final_status:
        print(final_status)
    elif not rows:
        print("No response received.")

    if not rows:
        return 0

    metrics = compute_metrics(rows, args.threshold_fraction)
    write_rows(paths["csv"], rows)
    final_plot(rows, metrics, paths["plot"], f"OP598 response: {label}")
    write_summary(paths["summary_csv"], paths["summary_md"], command, metadata, metrics, paths)

    print(f"CSV: {paths['csv']}")
    print(f"Summary CSV: {paths['summary_csv']}")
    print(f"Summary MD: {paths['summary_md']}")
    print(f"Plot: {paths['plot']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture OP598 sensor response profiles from the ESP32 over serial."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0", help="ESP32 serial port")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate")
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial read timeout")
    parser.add_argument("--read-wait", type=float, default=2.0, help="Idle wait extension while streaming")
    parser.add_argument("--startup-wait", type=float, default=1.0, help="Wait before serial setup")
    parser.add_argument("--soft-reboot", action="store_true", help="Send Ctrl-C and Ctrl-D before capture")
    parser.add_argument("--reboot-wait", type=float, default=2.0, help="Wait after soft reboot")
    parser.add_argument("--dtr", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--rts", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--no-reset-input", action="store_false", dest="reset_input")
    parser.set_defaults(reset_input=True)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for CSV, plots and summaries")
    parser.add_argument("--live-plot", action="store_true", help="Show a live matplotlib plot when a GUI display is available")
    parser.add_argument("--plot-every", type=int, default=25, help="Refresh live plot every N samples")
    parser.add_argument("--print-every", type=int, default=50, help="Print live text status every N samples")
    parser.add_argument("--threshold-fraction", type=float, default=0.5, help="Threshold as a fraction between baseline and peak")
    parser.add_argument("--verbose", action="store_true", help="Print every raw firmware line")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser("status", help="Query sensor status only")

    sample_parser = subparsers.add_parser("sample", help="Capture a simple ADC sample stream")
    sample_parser.add_argument("--sample-count", type=int, default=200, help="Number of ADC samples")
    sample_parser.add_argument("--sample-delay", type=int, default=1, help="Delay between samples")
    sample_parser.add_argument("--sample-unit", choices=("us", "ms"), default="ms", help="Delay unit")

    for name in ("pulse", "train", "random-train"):
        mode_parser = subparsers.add_parser(name, help=f"Run the {name} OP598 profile")
        if name != "pulse":
            mode_parser.add_argument("--count", type=int, default=5, help="Pulse count")
        if name == "train":
            mode_parser.add_argument("--period-ms", type=int, default=1000, help="Fixed train period")
        if name == "random-train":
            mode_parser.add_argument("--min-period-ms", type=int, default=1800, help="Minimum dark interval period")
            mode_parser.add_argument("--max-period-ms", type=int, default=2100, help="Maximum dark interval period")
        mode_parser.add_argument("--duration-ms", type=int, default=40, help="LED pulse duration")
        mode_parser.add_argument("--duty", type=int, default=1023, help="LED PWM duty 0-1023")
        mode_parser.add_argument("--pre-ms", type=int, default=40, help="Dark baseline before first pulse")
        mode_parser.add_argument("--post-ms", type=int, default=80, help="Dark tail after final pulse")
        mode_parser.add_argument("--sample-us", type=int, default=1000, help="Requested sampling interval in microseconds")

    return parser.parse_args()


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    sys.exit(main())
