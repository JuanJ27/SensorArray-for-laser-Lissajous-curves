from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analysis.aggregate import (
    CAMERA0_THRESHOLD_CAMPAIGN_ID,
    FIXED_PULSES_PER_DUTY,
    REQUIRED_CAMERA0_DUTIES,
    REQUIRED_CAMERA0_PER_PULSE_COLUMNS,
    REQUIRED_CAMERA0_THRESHOLD_COLUMNS,
    REQUIRED_CAMERA0_VALIDATION_COLUMNS,
    REQUIRED_CAMERA0_WILSON_COLUMNS,
    generate_camera0_threshold_artifacts,
)
from tools.run_led_intensity_sweep import build_camera0_campaign_plan, emit_plan_only


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def test_emit_plan_only_writes_camera0_campaign_plan_with_fixed_60(tmp_path: Path):
    plan_path = tmp_path / "camera0_intensity_campaign_plan.csv"
    args = argparse.Namespace(
        campaign_id=CAMERA0_THRESHOLD_CAMPAIGN_ID,
        run_intent="threshold",
        index=0,
        plan_seed=7,
        plan_output=str(plan_path),
    )

    exit_code = emit_plan_only(args)
    assert exit_code == 0
    assert plan_path.exists()

    header, rows = _read_csv(plan_path)
    assert "campaign_id" in header
    assert "camera_index" in header
    assert len(rows) == len(REQUIRED_CAMERA0_DUTIES) * FIXED_PULSES_PER_DUTY

    per_duty_counts = {duty: 0 for duty in REQUIRED_CAMERA0_DUTIES}
    for row in rows:
        assert row["campaign_id"] == CAMERA0_THRESHOLD_CAMPAIGN_ID
        assert int(row["camera_index"]) == 0
        per_duty_counts[int(row["duty"])] += 1
    assert all(count == FIXED_PULSES_PER_DUTY for count in per_duty_counts.values())


def test_generate_camera0_threshold_artifacts_writes_required_csvs_and_spanish_summary(tmp_path: Path):
    plan = build_camera0_campaign_plan(
        campaign_id=CAMERA0_THRESHOLD_CAMPAIGN_ID,
        camera_index=0,
        pulses_per_duty=FIXED_PULSES_PER_DUTY,
        seed=7,
    )
    fixture_rows = []
    for row in plan:
        duty = int(row["duty"])
        detected = duty >= 8 or (duty in {6, 7} and int(row["pulse_index"]) % 3 == 0)
        fixture_rows.append(
            {
                "run_id": f"run-{row['block_id']}",
                "campaign_id": row["campaign_id"],
                "camera_index": row["camera_index"],
                "duty": duty,
                "pulse_index": row["pulse_index"],
                "detected_any": str(detected).lower(),
                "detected_frames": 1 if detected else 0,
                "detection_events": 1 if detected else 0,
                "expected_pulses": 1,
                "block_id": row["block_id"],
                "block_order": row["block_order"],
                "acquisition_fingerprint": "fps30-exp10",
            }
        )

    result = generate_camera0_threshold_artifacts(fixture_rows, studies_dir=tmp_path)
    paths = result["paths"]

    per_pulse_header, per_pulse_rows = _read_csv(Path(paths["camera0_intensity_per_pulse"]))
    assert list(REQUIRED_CAMERA0_PER_PULSE_COLUMNS) == per_pulse_header
    assert len(per_pulse_rows) == len(fixture_rows)

    by_duty_header, by_duty_rows = _read_csv(Path(paths["camera0_intensity_by_duty_wilson"]))
    assert list(REQUIRED_CAMERA0_WILSON_COLUMNS) == by_duty_header
    assert len(by_duty_rows) == len(REQUIRED_CAMERA0_DUTIES)

    threshold_header, threshold_rows = _read_csv(Path(paths["camera0_threshold_estimates"]))
    assert list(REQUIRED_CAMERA0_THRESHOLD_COLUMNS) == threshold_header
    assert len(threshold_rows) == 1

    validation_header, validation_rows = _read_csv(Path(paths["camera0_validation_report"]))
    assert list(REQUIRED_CAMERA0_VALIDATION_COLUMNS) == validation_header
    assert len(validation_rows) == 1
    assert "camera0" in validation_rows[0]["resumen_es"].lower()

    ci_plot_path = Path(paths["camera0_duty_detection_ci_plot"])
    bootstrap_plot_path = Path(paths["camera0_threshold_bootstrap_plot"])
    summary_path = Path(paths["camera0_intensity_threshold_summary"])

    assert ci_plot_path.exists()
    assert bootstrap_plot_path.exists()
    assert ci_plot_path.suffix == ".png"
    assert bootstrap_plot_path.suffix == ".png"

    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Análisis estadístico" in summary_text
    assert "barras de error" in summary_text
    assert "camera0_duty_detection_ci.png" in summary_text
    assert "camera0_threshold_bootstrap.png" in summary_text
