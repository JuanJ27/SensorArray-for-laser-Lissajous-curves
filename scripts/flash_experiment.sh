#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python tools/run_led_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --count 5 --period-ms 1000 --duration-ms 300 --duty 1023 \
  --preview \
  --save-detected-frames \
  --frames-dir data/webcam/flash_presentation/demo
