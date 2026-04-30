"""
Sube hardware/latency_test.py a la ESP32 como main.py y elimina archivos viejos.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

import serial


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "hardware" / "latency_test.py"
DELETE_FILES = ("main.py", "latency_test.py", "sensor_data.csv", "laser.csv")


def read_until_prompt(serial_port: serial.Serial, timeout: float = 5.0) -> bytes:
    deadline = time.time() + timeout
    data = b""

    while time.time() < deadline:
        waiting = serial_port.in_waiting
        if waiting:
            data += serial_port.read(waiting)
            if data.endswith(b">"):
                return data
        else:
            time.sleep(0.02)

    return data


def raw_exec(serial_port: serial.Serial, code: str, timeout: float = 5.0) -> bytes:
    serial_port.write(code.encode("utf-8") + b"\x04")
    serial_port.flush()
    return read_until_prompt(serial_port, timeout=timeout)


def upload_main(port: str, baud: int) -> int:
    source = SOURCE_FILE.read_bytes()
    chunks = [source[i : i + 128] for i in range(0, len(source), 128)]

    with serial.Serial(port, baud, timeout=1) as serial_port:
        time.sleep(2.0)
        serial_port.reset_input_buffer()
        serial_port.write(b"\r\x03\x03\r\x01")
        serial_port.flush()
        time.sleep(0.5)
        banner = read_until_prompt(serial_port, timeout=5.0)
        print("Entrando a raw REPL...")
        print(banner.decode("utf-8", errors="ignore"))

        delete_code = (
            "import os\n"
            "for name in {}:\n"
            "    try:\n"
            "        os.remove(name)\n"
            "        print('REMOVED', name)\n"
            "    except OSError:\n"
            "        print('MISSING', name)\n"
        ).format(repr(DELETE_FILES))
        print(raw_exec(serial_port, delete_code, timeout=5.0).decode("utf-8", errors="ignore"))

        print(
            raw_exec(
                serial_port,
                "f=open('main.py','wb')\nf.close()\nprint('MAIN_TRUNCATED')",
                timeout=5.0,
            ).decode("utf-8", errors="ignore")
        )

        for chunk in chunks:
            code = (
                "import ubinascii\n"
                "f=open('main.py','ab')\n"
                "f.write(ubinascii.unhexlify('{}'))\n"
                "f.close()\n"
                "print('OK')"
            ).format(chunk.hex())
            output = raw_exec(serial_port, code, timeout=5.0)
            if b"Traceback" in output:
                print(output.decode("utf-8", errors="ignore"))
                return 1

        verify_code = (
            "import os\n"
            "source=open('main.py').read()\n"
            "print('MAIN_SIZE', os.stat('main.py')[6])\n"
            "compile(source, 'main.py', 'exec')\n"
            "print('COMPILE_OK')\n"
            "print(os.listdir())\n"
        )
        print(raw_exec(serial_port, verify_code, timeout=8.0).decode("utf-8", errors="ignore"))

        serial_port.write(b"\x02")
        serial_port.flush()
        time.sleep(0.2)
        serial_port.write(b"\x04")
        serial_port.flush()
        time.sleep(2.0)
        startup = serial_port.read(serial_port.in_waiting or 1)
        print("Salida inicial tras reinicio:\n")
        print(startup.decode("utf-8", errors="ignore"))

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube latency_test.py a la ESP32 como main.py"
    )
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Puerto serie de la ESP32")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate serie")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return upload_main(args.port, args.baud)


if __name__ == "__main__":
    sys.exit(main())
