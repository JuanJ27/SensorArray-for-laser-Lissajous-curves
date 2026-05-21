#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python tools/run_led_intensity_sweep.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --duties 8,16,24,32,48,64,96,128,192,256,384,512,768,1023 \
  --count 3 --period-ms 700 --duration-ms 200 \
  --preview \
  --save-detected-frames \
  --frames-dir data/webcam/flash_presentation/intensity
