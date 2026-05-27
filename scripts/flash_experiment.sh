#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

printf '[NON-PRODUCTION] scripts/flash_experiment.sh ejecuta demo webcam-only (run_intent=demo).\n' >&2
printf '[NON-PRODUCTION] No genera manifests de campaña ni habilita registro de producción.\n' >&2

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
