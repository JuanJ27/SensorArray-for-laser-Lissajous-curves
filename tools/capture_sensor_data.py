"""
Captura datos CSV emitidos por el ESP32 y los guarda en la PC.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import sys
import time

import serial


CSV_HEADER = "tiempo,azul,verde,amarillo,naranja,rojo"
CSV_ROW_PATTERN = re.compile(r"^\d+(,\d+){5}$")


def build_output_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = output_dir / f"sensor_data_{timestamp}.csv"
    if not base_path.exists():
        return base_path

    suffix = 1
    while True:
        candidate = output_dir / f"sensor_data_{timestamp}_{suffix:02d}.csv"
        if not candidate.exists():
            return candidate
        suffix += 1


def reset_board(serial_port: serial.Serial) -> None:
    serial_port.write(b"\x03\x03")
    time.sleep(0.2)
    serial_port.reset_input_buffer()
    serial_port.write(b"\x04")
    serial_port.flush()


def capture_stream(port: str, baudrate: int, output_dir: Path, reset: bool) -> int:
    output_path = build_output_path(output_dir)
    header_seen = False
    rows_written = 0

    with serial.Serial(port, baudrate=baudrate, timeout=1) as serial_port:
        time.sleep(2.0)
        if reset:
            reset_board(serial_port)

        print(f"Capturando desde {port} a {baudrate} baudios")
        print(f"Archivo de salida: {output_path}")
        print("Presiona Ctrl+C para detener la captura.\n")

        with output_path.open("w", encoding="utf-8", newline="") as output_file:
            try:
                while True:
                    raw_line = serial_port.readline()
                    if not raw_line:
                        continue

                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    print(line)

                    if line == CSV_HEADER:
                        if not header_seen:
                            output_file.write(line + "\n")
                            output_file.flush()
                            header_seen = True
                        continue

                    if CSV_ROW_PATTERN.match(line):
                        if not header_seen:
                            output_file.write(CSV_HEADER + "\n")
                            header_seen = True
                        output_file.write(line + "\n")
                        output_file.flush()
                        rows_written += 1
            except KeyboardInterrupt:
                serial_port.write(b"\x03")
                serial_port.flush()
                print("\nCaptura detenida por el usuario.")

    print(f"Filas guardadas en PC: {rows_written}")
    print(f"CSV final: {output_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Captura el stream CSV del ESP32 y lo guarda en la PC."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Puerto serie del ESP32")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate serie")
    parser.add_argument(
        "--output-dir",
        default="data/captures",
        help="Directorio donde guardar los CSV con timestamp",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="No reiniciar la placa al iniciar la captura",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return capture_stream(
        port=args.port,
        baudrate=args.baud,
        output_dir=Path(args.output_dir),
        reset=not args.no_reset,
    )


if __name__ == "__main__":
    sys.exit(main())
