"""
Captura resultados de latency_test desde el puerto serie y los guarda en la PC.

El ESP32 emite solo CSV minimo; el resumen se calcula en la PC.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import re
import sys
import time

import serial
from serial import SerialException


CSV_HEADER_PREFIX = "CSV_HEADER,"
CSV_ROW_PREFIX = "CSV_ROW,"
CSV_SUMMARY_PREFIX = "CSV_SUMMARY,"


def compute_median(values: list[float]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def safe_latency_value(raw_value: str) -> float | None:
    value = raw_value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def extract_latency_from_row(values: list[str], header: list[str] | None) -> tuple[float | None, str | None]:
    if not values:
        return None, None

    if header:
        status = None
        if "status" in header:
            status = values[header.index("status")].strip()
        if status and status != "ok":
            return None, status
        if "latency_us" in header:
            return safe_latency_value(values[header.index("latency_us")]), status
        return None, status

    if len(values) >= 2:
        return safe_latency_value(values[1]), None
    return None, None


DEFAULT_MIN_HEADER = ["trial", "latency_us", "adc"]
DEFAULT_FULL_HEADER = [
    "trial",
    "status",
    "latency_us",
    "freq_hz",
    "adc",
    "baseline_adc",
    "threshold",
    "dark_level",
    "lit_level",
    "contrast",
    "direction",
    "mode",
]


def default_header_for_row(values: list[str]) -> list[str]:
    if len(values) >= len(DEFAULT_FULL_HEADER):
        return DEFAULT_FULL_HEADER
    return DEFAULT_MIN_HEADER


def write_summary(summary_file, latencies: list[float], failures: int) -> None:
    writer = csv.writer(summary_file)
    writer.writerow(
        [
            "min_latency_us",
            "max_latency_us",
            "avg_latency_us",
            "median_latency_us",
            "failures",
            "min_freq_hz",
            "avg_freq_hz",
            "median_freq_hz",
            "max_freq_hz",
        ]
    )

    if not latencies:
        writer.writerow(["", "", "", "", failures, "", "", "", ""])
        return

    min_latency = min(latencies)
    max_latency = max(latencies)
    avg_latency = sum(latencies) / len(latencies)
    median_latency = compute_median(latencies)

    def to_freq(value: float) -> float:
        if value <= 0:
            return 0.0
        return 1_000_000.0 / value

    writer.writerow(
        [
            "{:.6f}".format(min_latency),
            "{:.6f}".format(max_latency),
            "{:.6f}".format(avg_latency),
            "{:.6f}".format(median_latency),
            failures,
            "{:.6f}".format(to_freq(min_latency)),
            "{:.6f}".format(to_freq(avg_latency)),
            "{:.6f}".format(to_freq(median_latency)),
            "{:.6f}".format(to_freq(max_latency)),
        ]
    )


def list_serial_candidates() -> list[str]:
    candidates = []
    for path in Path("/dev").iterdir():
        if re.match(r"tty(USB|ACM)\d+$", path.name):
            candidates.append(str(path))
    candidates.sort()
    return candidates


def resolve_port(requested_port: str) -> str:
    if Path(requested_port).exists():
        return requested_port

    candidates = list_serial_candidates()
    if len(candidates) == 1:
        return candidates[0]

    raise SerialException(
        "Puerto no disponible: {}. Puertos detectados: {}".format(
            requested_port,
            ", ".join(candidates) if candidates else "ninguno",
        )
    )


def build_output_paths(output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = output_dir / ("latency_results_" + timestamp + ".csv")
    summary_path = output_dir / ("latency_summary_" + timestamp + ".csv")
    log_path = output_dir / ("latency_log_" + timestamp + ".txt")

    suffix = 1
    while csv_path.exists() or summary_path.exists() or log_path.exists():
        label = "{}_{:02d}".format(timestamp, suffix)
        csv_path = output_dir / ("latency_results_" + label + ".csv")
        summary_path = output_dir / ("latency_summary_" + label + ".csv")
        log_path = output_dir / ("latency_log_" + label + ".txt")
        suffix += 1

    return csv_path, summary_path, log_path


def reset_board(serial_port: serial.Serial) -> None:
    serial_port.write(b"\x03\x03")
    time.sleep(0.2)
    serial_port.reset_input_buffer()
    serial_port.write(b"\x04")
    serial_port.flush()


def write_csv_row(writer: csv.writer, prefix: str, line: str) -> None:
    values = line[len(prefix) :].split(",")
    writer.writerow(values)


def open_serial_port(port: str, baudrate: int) -> serial.Serial:
    resolved_port = resolve_port(port)
    return serial.Serial(resolved_port, baudrate=baudrate, timeout=1)


def reopen_serial_port(port: str, baudrate: int, delay_s: float = 2.5) -> serial.Serial:
    time.sleep(delay_s)
    return open_serial_port(port, baudrate)


def capture_latency(port: str, baudrate: int, output_dir: Path, reset: bool) -> int:
    csv_path, summary_path, log_path = build_output_paths(output_dir)

    serial_port = open_serial_port(port, baudrate)
    active_port = serial_port.port
    time.sleep(2.0)
    if reset:
        reset_board(serial_port)
        serial_port.close()
        serial_port = reopen_serial_port(port, baudrate)
        active_port = serial_port.port

    print("Capturando latencia desde {} a {} baudios".format(active_port, baudrate))
    print("Resultados CSV: {}".format(csv_path))
    print("Resumen CSV: {}".format(summary_path))
    print("Log de consola: {}".format(log_path))
    print("Presiona Ctrl+C para detener la captura.\n")

    csv_writer = None
    summary_written = False
    header_fields = None
    header_written = False
    latencies: list[float] = []
    failures = 0

    with (
        csv_path.open("w", encoding="utf-8", newline="") as csv_file,
        summary_path.open("w", encoding="utf-8", newline="") as summary_file,
        log_path.open("w", encoding="utf-8") as log_file,
    ):
        try:
            while True:
                try:
                    raw_line = serial_port.readline()
                except SerialException:
                    try:
                        serial_port.close()
                    except Exception:
                        pass
                    print("\n[INFO] Puerto serie reconectandose...")
                    serial_port = reopen_serial_port(port, baudrate)
                    active_port = serial_port.port
                    print("[INFO] Reconectado a {}".format(active_port))
                    continue

                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="ignore").rstrip("\r\n")
                if not line:
                    continue

                print(line)
                log_file.write(line + "\n")
                log_file.flush()

                if line.startswith(CSV_HEADER_PREFIX):
                    if csv_writer is None:
                        csv_writer = csv.writer(csv_file)
                    header_fields = line[len(CSV_HEADER_PREFIX) :].split(",")
                    if not header_written:
                        csv_writer.writerow(header_fields)
                        csv_file.flush()
                        header_written = True
                    continue

                if line.startswith(CSV_ROW_PREFIX):
                    row_values = line[len(CSV_ROW_PREFIX) :].split(",")
                    if csv_writer is None:
                        csv_writer = csv.writer(csv_file)
                    if not header_written:
                        if header_fields is None:
                            header_fields = default_header_for_row(row_values)
                        csv_writer.writerow(header_fields)
                        csv_file.flush()
                        header_written = True

                    write_csv_row(csv_writer, CSV_ROW_PREFIX, line)
                    csv_file.flush()

                    latency_us, _status = extract_latency_from_row(row_values, header_fields)
                    if latency_us is None:
                        failures += 1
                    else:
                        latencies.append(latency_us)
                    continue

                if line.startswith(CSV_SUMMARY_PREFIX):
                    summary_writer = csv.writer(summary_file)
                    summary_writer.writerow(
                        [
                            "min_latency_us",
                            "max_latency_us",
                            "avg_latency_us",
                            "median_latency_us",
                            "failures",
                            "min_freq_hz",
                            "avg_freq_hz",
                            "median_freq_hz",
                            "max_freq_hz",
                        ]
                    )
                    write_csv_row(summary_writer, CSV_SUMMARY_PREFIX, line)
                    summary_file.flush()
                    summary_written = True
        except KeyboardInterrupt:
            try:
                serial_port.write(b"\x03")
                serial_port.flush()
            except Exception:
                pass
            print("\nCaptura detenida por el usuario.")
        finally:
            if not summary_written:
                write_summary(summary_file, latencies, failures)
                summary_file.flush()
            try:
                serial_port.close()
            except Exception:
                pass

    print("Archivos guardados en PC.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Captura resultados de latency_test y los guarda con fecha y hora."
    )
    parser.add_argument("--port", default="/dev/ttyUSB1", help="Puerto serie de la ESP32")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate serie")
    parser.add_argument(
        "--output-dir",
        default="data/latency_runs",
        help="Directorio donde guardar CSV y log de cada corrida",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="No reiniciar la placa al iniciar la captura",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return capture_latency(
        port=args.port,
        baudrate=args.baud,
        output_dir=Path(args.output_dir),
        reset=not args.no_reset,
    )


if __name__ == "__main__":
    sys.exit(main())
