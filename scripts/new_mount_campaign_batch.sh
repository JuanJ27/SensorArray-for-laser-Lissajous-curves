#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  printf 'Usage: %s <campaign-id> <dark-control-ref> [--preview] [--index <N>]\n' "$0"
  exit 1
fi

CAMPAIGN_ID="$1"
DARK_CONTROL_REF="$2"
PREVIEW_ARG=""
CAMERA_INDEX="2"
shift 2

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preview)
      PREVIEW_ARG="--preview"
      shift
      ;;
    --index)
      if [[ $# -lt 2 ]]; then
        printf 'Missing value for --index\n' >&2
        exit 1
      fi
      CAMERA_INDEX="$2"
      shift 2
      ;;
    *)
      printf 'Unsupported option: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

cd "$(dirname "$0")/.."
source .venv/bin/activate

MANIFEST_DIR="data/dual_experiments/new_mount_campaigns/${CAMPAIGN_ID}"
MANIFEST_PATH="${MANIFEST_DIR}/batch_manifest.json"
mkdir -p "${MANIFEST_DIR}"

python - "$CAMPAIGN_ID" "$MANIFEST_PATH" <<'PY'
import json
import sys
from pathlib import Path

from scripts.new_mount_campaign_batch import build_batch_plan

campaign_id = sys.argv[1]
manifest_path = Path(sys.argv[2])
manifest = build_batch_plan(campaign_id)
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Initialized batch manifest: {manifest_path}")
PY

BATCH_STARTED_AT="$(python - <<'PY'
from datetime import datetime
print(datetime.now().isoformat(timespec='seconds'))
PY
)"

for run_index in $(seq 1 10); do
  python tools/run_dual_flash_experiment.py \
    $PREVIEW_ARG \
    --index "$CAMERA_INDEX" \
    --run-intent production \
    --campaign-id "$CAMPAIGN_ID" \
    --mount-context new-camera-mount \
    --dark-control-ref "$DARK_CONTROL_REF" \
    --batch-started-at "$BATCH_STARTED_AT" \
    --run-index "$run_index" \
    random-train \
    --min-period-ms 1800 \
    --max-period-ms 2200 \
    --count 60 \
    --duration-ms 40
done
