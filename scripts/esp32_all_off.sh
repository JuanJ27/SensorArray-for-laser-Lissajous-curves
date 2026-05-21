#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python tools/led_serial_control.py --port /dev/ttyUSB0 --soft-reboot boardled off
python tools/led_serial_control.py --port /dev/ttyUSB0 --off
