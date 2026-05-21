#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python tools/run_flash_parameter_sweep.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --metric max --threshold-delta 30 \
  --duty 128 \
  --count 3 --period-ms 700 --duration-ms 100 \
  --exposure 10 --exposures 3,5,10,20,40 \
  --durations-ms 10,20,50,100,200,300 \
  --preview \
  --save-detected-frames \
  --frames-dir data/webcam/flash_presentation/parameters
