from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import run_dual_flash_experiment as dual


def _write_manifest(run_dir: Path, payload: dict[str, object]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def _base_dark_control_manifest(created_at: datetime) -> dict[str, object]:
    return {
        "run_id": "dark_run_001",
        "created_at": created_at.isoformat(timespec="seconds"),
        "mode": "random-train",
        "campaign_id": "new-camera-mount-20260526",
        "mount_context": "new-camera-mount",
        "run_intent": "dark-control",
        "dark_control_ref": None,
        "run_index": 0,
        "config_fingerprint": "abc123",
    }


def test_gate_blocks_when_dark_control_ref_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="dark_control_ref"):
        dual.validate_dark_control_gate(
            output_root=tmp_path,
            campaign_id="new-camera-mount-20260526",
            mount_context="new-camera-mount",
            dark_control_ref="",
            config_fingerprint="abc123",
            production_started_at=datetime(2026, 5, 26, 10, 0, 0),
            freshness_minutes=5,
        )


def test_gate_blocks_when_dark_control_is_stale(tmp_path: Path) -> None:
    production_started_at = datetime(2026, 5, 26, 10, 0, 0)
    stale_created_at = production_started_at - timedelta(minutes=6)
    payload = _base_dark_control_manifest(stale_created_at)
    _write_manifest(tmp_path / "dark_run_001", payload)

    with pytest.raises(ValueError, match="stale"):
        dual.validate_dark_control_gate(
            output_root=tmp_path,
            campaign_id="new-camera-mount-20260526",
            mount_context="new-camera-mount",
            dark_control_ref="dark_run_001",
            config_fingerprint="abc123",
            production_started_at=production_started_at,
            freshness_minutes=5,
        )


def test_gate_blocks_when_mount_context_mismatch(tmp_path: Path) -> None:
    production_started_at = datetime(2026, 5, 26, 10, 0, 0)
    payload = _base_dark_control_manifest(production_started_at - timedelta(minutes=1))
    payload["mount_context"] = "legacy-mount"
    _write_manifest(tmp_path / "dark_run_001", payload)

    with pytest.raises(ValueError, match="mount_context"):
        dual.validate_dark_control_gate(
            output_root=tmp_path,
            campaign_id="new-camera-mount-20260526",
            mount_context="new-camera-mount",
            dark_control_ref="dark_run_001",
            config_fingerprint="abc123",
            production_started_at=production_started_at,
            freshness_minutes=5,
        )


def test_gate_accepts_exact_five_minute_boundary(tmp_path: Path) -> None:
    production_started_at = datetime(2026, 5, 26, 10, 0, 0)
    boundary_created_at = production_started_at - timedelta(minutes=5)
    payload = _base_dark_control_manifest(boundary_created_at)
    _write_manifest(tmp_path / "dark_run_001", payload)

    resolved = dual.validate_dark_control_gate(
        output_root=tmp_path,
        campaign_id="new-camera-mount-20260526",
        mount_context="new-camera-mount",
        dark_control_ref="dark_run_001",
        config_fingerprint="abc123",
        production_started_at=production_started_at,
        freshness_minutes=5,
    )

    assert resolved["run_id"] == "dark_run_001"


def test_gate_accepts_stale_by_run_when_batch_start_is_fresh(tmp_path: Path) -> None:
    dark_created_at = datetime(2026, 5, 26, 10, 0, 0)
    batch_started_at = datetime(2026, 5, 26, 10, 4, 0)
    production_started_at = datetime(2026, 5, 26, 10, 7, 0)
    payload = _base_dark_control_manifest(dark_created_at)
    _write_manifest(tmp_path / "dark_run_001", payload)

    resolved = dual.validate_dark_control_gate(
        output_root=tmp_path,
        campaign_id="new-camera-mount-20260526",
        mount_context="new-camera-mount",
        dark_control_ref="dark_run_001",
        config_fingerprint="abc123",
        production_started_at=production_started_at,
        freshness_minutes=5,
        batch_started_at=batch_started_at,
    )

    assert resolved["run_id"] == "dark_run_001"


def test_gate_blocks_when_dark_control_is_stale_at_batch_start(tmp_path: Path) -> None:
    dark_created_at = datetime(2026, 5, 26, 10, 0, 0)
    batch_started_at = datetime(2026, 5, 26, 10, 6, 0)
    production_started_at = datetime(2026, 5, 26, 10, 7, 0)
    payload = _base_dark_control_manifest(dark_created_at)
    _write_manifest(tmp_path / "dark_run_001", payload)

    with pytest.raises(ValueError, match="stale"):
        dual.validate_dark_control_gate(
            output_root=tmp_path,
            campaign_id="new-camera-mount-20260526",
            mount_context="new-camera-mount",
            dark_control_ref="dark_run_001",
            config_fingerprint="abc123",
            production_started_at=production_started_at,
            freshness_minutes=5,
            batch_started_at=batch_started_at,
        )
