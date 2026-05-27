from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import run_dual_flash_experiment as dual


def _base_args() -> argparse.Namespace:
    return argparse.Namespace(
        run_intent="production",
        campaign_id="new-camera-mount-20260526",
        mount_context="new-camera-mount",
        dark_control_ref="dark_run_001",
        run_index=1,
        mode="random-train",
        index=2,
        width=640,
        height=480,
        fps=30,
        fourcc="YUYV",
        metric="max",
        threshold_delta=30.0,
        sigma_multiplier=1.0,
        warmup=1.0,
        calibration=3.0,
        trigger_delay=1.0,
        tail_seconds=2.0,
        port="/dev/ttyUSB0",
        baud=115200,
        count=30,
        min_period_ms=1800,
        max_period_ms=2200,
        duration_ms=40,
        duty=1023,
        pre_ms=40,
        post_ms=120,
        sample_us=1000,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("campaign_id", ""),
        ("mount_context", ""),
        ("dark_control_ref", ""),
    ],
)
def test_production_metadata_requires_non_empty_strings(field: str, value: str) -> None:
    args = _base_args()
    setattr(args, field, value)

    with pytest.raises(ValueError, match=field):
        dual.validate_production_metadata(args)


def test_production_metadata_requires_positive_run_index() -> None:
    args = _base_args()
    args.run_index = 0

    with pytest.raises(ValueError, match="run_index"):
        dual.validate_production_metadata(args)


def test_production_metadata_contains_required_fields_and_fingerprint() -> None:
    args = _base_args()

    metadata = dual.validate_production_metadata(args)

    assert metadata["campaign_id"] == "new-camera-mount-20260526"
    assert metadata["mount_context"] == "new-camera-mount"
    assert metadata["run_intent"] == "production"
    assert metadata["dark_control_ref"] == "dark_run_001"
    assert metadata["run_index"] == 1
    assert metadata["config_fingerprint"]
    assert metadata["acquisition_config_fingerprint"]


def test_dark_control_metadata_contains_required_fields_and_fingerprint() -> None:
    args = _base_args()
    args.run_intent = "dark-control"
    args.dark_control_ref = None
    args.run_index = 0

    metadata = dual.validate_run_metadata(args)

    assert metadata["campaign_id"] == "new-camera-mount-20260526"
    assert metadata["mount_context"] == "new-camera-mount"
    assert metadata["run_intent"] == "dark-control"
    assert metadata["dark_control_ref"] is None
    assert metadata["run_index"] == 0
    assert metadata["config_fingerprint"]
    assert metadata["acquisition_config_fingerprint"]


def test_write_manifest_persists_dark_control_metadata_for_gate_reference(tmp_path: Path) -> None:
    args = _base_args()
    args.run_intent = "dark-control"
    args.dark_control_ref = None
    args.run_index = 0

    run_dir = tmp_path / "random-train_20260526_120000"
    run_dir.mkdir(parents=True)
    manifest_path = run_dir / "manifest.json"
    metadata = dual.validate_run_metadata(args)

    dual.write_manifest(
        paths={
            "run_dir": run_dir,
            "manifest": manifest_path,
        },
        args=args,
        webcam_summary={"frames": 1},
        op598_summary={},
        pulse_events=[],
        coincidence_rows=[],
        visuals_status={},
        run_metadata=metadata,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    created_at = datetime.fromisoformat(payload["created_at"])
    assert created_at
    assert payload["run_intent"] == "dark-control"
    assert payload["campaign_id"] == "new-camera-mount-20260526"
    assert payload["mount_context"] == "new-camera-mount"
    assert payload["config_fingerprint"] == metadata["config_fingerprint"]


def test_dark_control_manifest_written_by_intent_satisfies_production_gate(tmp_path: Path) -> None:
    dark_args = _base_args()
    dark_args.run_intent = "dark-control"
    dark_args.dark_control_ref = None
    dark_args.run_index = 0
    dark_args.duty = 0

    production_args = _base_args()
    dark_metadata = dual.validate_run_metadata(dark_args)
    production_metadata = dual.validate_production_metadata(production_args)

    run_dir = tmp_path / "random-train_20260526_120000"
    run_dir.mkdir(parents=True)
    manifest_path = run_dir / "manifest.json"
    dual.write_manifest(
        paths={"run_dir": run_dir, "manifest": manifest_path},
        args=dark_args,
        webcam_summary={"frames": 1},
        op598_summary={},
        pulse_events=[],
        coincidence_rows=[],
        visuals_status={},
        run_metadata=dark_metadata,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["run_id"] = "dark_run_001"
    payload["created_at"] = "2026-05-26T10:00:00"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    resolved = dual.validate_dark_control_gate(
        output_root=tmp_path,
        campaign_id="new-camera-mount-20260526",
        mount_context="new-camera-mount",
        dark_control_ref="dark_run_001",
        config_fingerprint=str(production_metadata["config_fingerprint"]),
        acquisition_config_fingerprint=str(production_metadata["acquisition_config_fingerprint"]),
        production_started_at=datetime(2026, 5, 26, 10, 4, 0),
        freshness_minutes=5,
    )
    assert resolved["run_intent"] == "dark-control"


def test_dark_control_gate_rejects_real_camera_profile_mismatch_even_if_duty_diff_is_allowed(
    tmp_path: Path,
) -> None:
    dark_args = _base_args()
    dark_args.run_intent = "dark-control"
    dark_args.dark_control_ref = None
    dark_args.run_index = 0
    dark_args.duty = 0

    production_args = _base_args()
    production_args.fps = 25

    dark_metadata = dual.validate_run_metadata(dark_args)
    production_metadata = dual.validate_production_metadata(production_args)

    run_dir = tmp_path / "random-train_20260526_120000"
    run_dir.mkdir(parents=True)
    manifest_path = run_dir / "manifest.json"
    dual.write_manifest(
        paths={"run_dir": run_dir, "manifest": manifest_path},
        args=dark_args,
        webcam_summary={"frames": 1},
        op598_summary={},
        pulse_events=[],
        coincidence_rows=[],
        visuals_status={},
        run_metadata=dark_metadata,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["run_id"] = "dark_run_001"
    payload["created_at"] = "2026-05-26T10:00:00"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="config_fingerprint mismatch"):
        dual.validate_dark_control_gate(
            output_root=tmp_path,
            campaign_id="new-camera-mount-20260526",
            mount_context="new-camera-mount",
            dark_control_ref="dark_run_001",
            config_fingerprint=str(production_metadata["config_fingerprint"]),
            acquisition_config_fingerprint=str(production_metadata["acquisition_config_fingerprint"]),
            production_started_at=datetime(2026, 5, 26, 10, 4, 0),
            freshness_minutes=5,
        )
