"""
Send LED pulse commands to an ESP32 running hardware/led_pulse_controller.py.
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit("pyserial is not installed. Run: python -m pip install -r requirements.txt") from exc


def read_available(port: serial.Serial, wait: float) -> str:
    deadline = time.time() + wait
    chunks: list[bytes] = []
    while time.time() < deadline:
        waiting = port.in_waiting
        if waiting:
            chunks.append(port.read(waiting))
            deadline = time.time() + 0.1
        else:
            time.sleep(0.02)
    return b"".join(chunks).decode("utf-8", errors="replace")


def send_command(port: serial.Serial, command: str, wait: float) -> str:
    port.write((command.strip() + "\n").encode("utf-8"))
    port.flush()
    return read_available(port, wait)


def command_from_args(args: argparse.Namespace) -> str:
    if args.command:
        return " ".join(args.command)
    if args.duty is not None:
        return f"set duty {args.duty}"
    if args.freq is not None:
        return f"set freq {args.freq}"
    if args.pulse:
        duration_ms, duty = args.pulse
        return f"pulse {duration_ms} {duty}"
    if args.train:
        count, period_ms, duration_ms, duty = args.train
        return f"train {count} {period_ms} {duration_ms} {duty}"
    if args.off:
        return "off"
    return "status"


def effective_read_wait(args: argparse.Namespace) -> float:
    wait = args.read_wait
    if args.pulse:
        duration_ms, _ = args.pulse
        wait = max(wait, duration_ms / 1000.0 + 1.0)
    if args.train:
        count, period_ms, duration_ms, _ = args.train
        train_ms = max(0, count - 1) * period_ms + duration_ms
        wait = max(wait, train_ms / 1000.0 + 1.0)
    return wait


def run(args: argparse.Namespace) -> int:
    command = command_from_args(args)
    with serial.Serial(args.port, args.baud, timeout=args.timeout) as serial_port:
        serial_port.dtr = args.dtr
        serial_port.rts = args.rts
        if args.soft_reboot:
            time.sleep(args.startup_wait)
            serial_port.write(b"\x03")
            serial_port.flush()
            time.sleep(0.2)
            serial_port.write(b"\x04")
            serial_port.flush()
            time.sleep(args.reboot_wait)
        if args.reset_input:
            time.sleep(args.startup_wait)
            serial_port.reset_input_buffer()
        output = send_command(serial_port, command, effective_read_wait(args))

    print(f"> {command}")
    if output.strip():
        print(output.rstrip())
    else:
        print("No response received.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control an ESP32 LED pulse controller over serial."
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Raw command to send, e.g. status or boardled off",
    )
    parser.add_argument("--port", default="/dev/ttyUSB0", help="ESP32 serial port")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate")
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial read timeout")
    parser.add_argument("--read-wait", type=float, default=1.0, help="Seconds to wait for ACK")
    parser.add_argument("--startup-wait", type=float, default=1.0, help="Wait before clearing input")
    parser.add_argument(
        "--soft-reboot",
        action="store_true",
        help="Send Ctrl-C then Ctrl-D before the command to restart MicroPython main.py",
    )
    parser.add_argument("--reboot-wait", type=float, default=2.0, help="Wait after soft reboot")
    parser.add_argument(
        "--dtr",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Serial DTR line state. Default keeps this ESP32 out of bootloader",
    )
    parser.add_argument(
        "--rts",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Serial RTS line state. Default keeps this ESP32 out of bootloader",
    )
    parser.add_argument(
        "--no-reset-input",
        action="store_false",
        dest="reset_input",
        help="Do not clear pending serial input before sending",
    )
    parser.set_defaults(reset_input=True)
    parser.add_argument("--duty", type=int, help="Shortcut for: set duty <value>")
    parser.add_argument("--freq", type=int, help="Shortcut for: set freq <hz>")
    parser.add_argument(
        "--pulse",
        nargs=2,
        type=int,
        metavar=("DURATION_MS", "DUTY"),
        help="Shortcut for: pulse <duration_ms> <duty>",
    )
    parser.add_argument(
        "--train",
        nargs=4,
        type=int,
        metavar=("COUNT", "PERIOD_MS", "DURATION_MS", "DUTY"),
        help="Shortcut for: train <count> <period_ms> <duration_ms> <duty>",
    )
    parser.add_argument("--off", action="store_true", help="Shortcut for: off")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
