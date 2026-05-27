from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from analysis import aggregate, reconstruction


def _write_dual_run(root: Path, run_id: str, metadata: dict[str, str]) -> None:
    run_dir = root / "data" / "dual_experiments" / "phase2_statistical_reconstruction_matrix" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    with (run_dir / "coincidence_table.csv").open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=("window_frame_count", "matched_frame_detected", "detected_in_window", "matched_frame_dt_ms"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "window_frame_count": "3",
                "matched_frame_detected": "true",
                "detected_in_window": "true",
                "matched_frame_dt_ms": "12.5",
            }
        )

    with (run_dir / "dual_summary.csv").open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(("field", "value"))
        writer.writerow(("mode", "random-train"))
        writer.writerow(("op598.metadata.count", "1"))
        writer.writerow(("op598.metadata.duty", "1023"))
        writer.writerow(("op598.metadata.duration_ms", "40"))
        for key, value in metadata.items():
            writer.writerow((f"production.{key}", value))

    manifest = {
        "run_id": run_id,
        **metadata,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_collect_dual_random_train_propagates_campaign_metadata_and_filters_by_campaign(tmp_path: Path) -> None:
    _write_dual_run(
        tmp_path,
        "random-train_20260526_100000",
        {
            "campaign_id": "new-camera-mount-20260526",
            "mount_context": "new-camera-mount",
            "run_intent": "production",
            "dark_control_ref": "dark_run_001",
            "run_index": "1",
        },
    )
    _write_dual_run(
        tmp_path,
        "random-train_20260526_100100",
        {
            "campaign_id": "legacy-campaign-20260520",
            "mount_context": "legacy-mount",
            "run_intent": "production",
            "dark_control_ref": "legacy_dark_001",
            "run_index": "9",
        },
    )

    rows, _ = aggregate.collect_dual_random_train(tmp_path, campaign_id="new-camera-mount-20260526")

    assert len(rows) == 1
    assert rows[0]["campaign_id"] == "new-camera-mount-20260526"
    assert rows[0]["mount_context"] == "new-camera-mount"
    assert rows[0]["dark_control_ref"] == "dark_run_001"
    assert rows[0]["run_intent"] == "production"
    assert rows[0]["run_index"] == 1


def test_reconstruction_fails_closed_when_new_mount_filter_is_missing() -> None:
    dual_runs = [
        {"campaign_id": "new-camera-mount-20260526", "mount_context": "new-camera-mount"},
    ]

    with pytest.raises(ValueError, match="campaign filter"):
        reconstruction.require_campaign_filter_for_new_mount(dual_runs, campaign_id=None)
