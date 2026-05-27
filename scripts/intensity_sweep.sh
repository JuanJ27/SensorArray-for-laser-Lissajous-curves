#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

CAMPAIGN_ID="${CAMPAIGN_ID:-camera0-intensity-threshold-statistics}"
MODE="${1:-plan}"

usage() {
  cat <<'EOF'
Uso: scripts/intensity_sweep.sh [plan|preflight|live]

Wrapper de campaña camera0 para umbral de intensidad (sin pooling legado).

Modos:
  plan       Genera y previsualiza el plan offline (NO hardware).
  preflight  Ejecuta checks previos + plan offline (NO hardware).
  live       Requiere confirmación explícita de operador para habilitar hardware.

Gates obligatorios para modo live:
  1) CAMPAIGN_ID no vacío y trazable
  2) LIVE_ACQUISITION=1
  3) OPERADOR_CONFIRMA_LIVE=SI

Safeguards:
  - --campaign-id ${CAMPAIGN_ID}
  - --run-intent threshold
  - --index 0 (cámara fija)
  - no pooling legado entre campañas
EOF
}

printf '[SAFETY] Wrapper camera0 threshold campaign.\n' >&2
printf '[SAFETY] Default mode is plan/preflight (no live acquisition).\n' >&2
printf '[SAFETY] To execute live sweep you MUST set LIVE_ACQUISITION=1 and mode=live.\n' >&2

if [[ "$MODE" == "-h" || "$MODE" == "--help" || "$MODE" == "help" ]]; then
  usage
  exit 0
fi

if [[ -z "${CAMPAIGN_ID}" ]]; then
  printf '[BLOCKED] CAMPAIGN_ID vacío: no se permite ejecución sin identificador de campaña.\n' >&2
  exit 4
fi

printf '[PREVIEW] campaign_id=%s run_intent=threshold index=0\n' "$CAMPAIGN_ID" >&2

if [[ "$MODE" == "plan" ]]; then
  python tools/run_led_intensity_sweep.py \
    --campaign-id "$CAMPAIGN_ID" \
    --run-intent threshold \
    --index 0 \
    --emit-plan-only \
    --plan-output data/derived/studies/camera0_intensity_campaign_plan.csv
  exit 0
fi

if [[ "$MODE" == "preflight" ]]; then
  python tools/run_led_intensity_sweep.py \
    --campaign-id "$CAMPAIGN_ID" \
    --run-intent threshold \
    --index 0 \
    --emit-plan-only \
    --plan-output data/derived/studies/camera0_intensity_campaign_plan.csv
  printf '[PREFLIGHT] Plan generated only. No hardware execution performed.\n' >&2
  exit 0
fi

if [[ "$MODE" != "live" ]]; then
  printf '[ERROR] Unknown mode: %s (use plan|preflight|live)\n' "$MODE" >&2
  exit 2
fi

if [[ "${LIVE_ACQUISITION:-0}" != "1" ]]; then
  printf '[BLOCKED] LIVE_ACQUISITION=1 not set. Refusing to run hardware.\n' >&2
  exit 3
fi

if [[ "${OPERADOR_CONFIRMA_LIVE:-NO}" != "SI" ]]; then
  printf '[BLOCKED] Falta confirmación explícita: seteá OPERADOR_CONFIRMA_LIVE=SI para continuar.\n' >&2
  exit 5
fi

python tools/run_led_intensity_sweep.py \
  --port /dev/ttyUSB0 \
  --campaign-id "$CAMPAIGN_ID" \
  --run-intent threshold \
  --index 0 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --duties 0,1,2,3,4,5,6,7,8,10,12,16,24,32,48,64,128 \
  --count 60 --period-ms 700 --duration-ms 200 \
  --preview \
  --save-detected-frames \
  --frames-dir data/webcam/flash_presentation/intensity
