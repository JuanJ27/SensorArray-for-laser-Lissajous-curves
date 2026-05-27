from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts import new_mount_campaign_batch as batch


def test_build_batch_plan_has_exactly_ten_independent_runs() -> None:
    plan = batch.build_batch_plan(campaign_id="new-camera-mount-20260526")

    assert len(plan["runs"]) == 10
    assert [run["run_index"] for run in plan["runs"]] == list(range(1, 11))


def test_build_batch_plan_forces_120_second_random_train_window() -> None:
    plan = batch.build_batch_plan(campaign_id="new-camera-mount-20260526")

    for run in plan["runs"]:
        assert run["mode"] == "random-train"
        assert run["run_duration_s"] == 120
        assert run["min_period_ms"] == 1800
        assert run["max_period_ms"] == 2200


def test_batch_command_uses_production_metadata_and_dark_control_reference() -> None:
    command = batch.build_run_command(
        run_index=3,
        campaign_id="new-camera-mount-20260526",
        dark_control_ref="dark_run_001",
        batch_started_at="2026-05-26T10:04:00",
        camera_index=0,
    )

    assert "--index" in command and "0" in command
    assert "--run-intent" in command and "production" in command
    assert "--campaign-id" in command and "new-camera-mount-20260526" in command
    assert "--mount-context" in command and "new-camera-mount" in command
    assert "--dark-control-ref" in command and "dark_run_001" in command
    assert "--batch-started-at" in command and "2026-05-26T10:04:00" in command
    assert "--run-index" in command and "3" in command
    assert "--count" in command and "60" in command
