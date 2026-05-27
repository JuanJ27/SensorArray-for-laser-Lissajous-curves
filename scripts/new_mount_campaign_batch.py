from __future__ import annotations

from datetime import datetime


BATCH_TARGET_RUNS = 10
RUN_DURATION_SECONDS = 120
RANDOM_MIN_PERIOD_MS = 1800
RANDOM_MAX_PERIOD_MS = 2200
RANDOM_TRAIN_FLASH_COUNT = 60
MOUNT_CONTEXT = "new-camera-mount"


def build_batch_plan(campaign_id: str) -> dict[str, object]:
    runs = [
        {
            "run_index": run_index,
            "mode": "random-train",
            "run_duration_s": RUN_DURATION_SECONDS,
            "min_period_ms": RANDOM_MIN_PERIOD_MS,
            "max_period_ms": RANDOM_MAX_PERIOD_MS,
            "status": "pending",
        }
        for run_index in range(1, BATCH_TARGET_RUNS + 1)
    ]
    return {
        "campaign_id": campaign_id,
        "mount_context": MOUNT_CONTEXT,
        "batch_target_runs": BATCH_TARGET_RUNS,
        "run_duration_s": RUN_DURATION_SECONDS,
        "interval_bounds_ms": {
            "min": RANDOM_MIN_PERIOD_MS,
            "max": RANDOM_MAX_PERIOD_MS,
        },
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "runs": runs,
    }


def build_run_command(
    run_index: int,
    campaign_id: str,
    dark_control_ref: str,
    batch_started_at: str,
    camera_index: int,
) -> list[str]:
    return [
        "python",
        "tools/run_dual_flash_experiment.py",
        "--index",
        str(camera_index),
        "--run-intent",
        "production",
        "--campaign-id",
        campaign_id,
        "--mount-context",
        MOUNT_CONTEXT,
        "--dark-control-ref",
        dark_control_ref,
        "--batch-started-at",
        batch_started_at,
        "--run-index",
        str(run_index),
        "random-train",
        "--count",
        str(RANDOM_TRAIN_FLASH_COUNT),
        "--min-period-ms",
        str(RANDOM_MIN_PERIOD_MS),
        "--max-period-ms",
        str(RANDOM_MAX_PERIOD_MS),
        "--duration-ms",
        "40",
    ]
