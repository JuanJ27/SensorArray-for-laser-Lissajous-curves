from analysis.aggregate import (
    FIXED_PULSES_PER_DUTY,
    REQUIRED_CAMERA0_DUTIES,
    REQUIRED_CAMERA0_PLAN_COLUMNS,
    validate_camera0_plan_rows,
)


def _build_plan(pulses_per_duty: int = FIXED_PULSES_PER_DUTY):
    rows = []
    for block_id in range(3):
        for duty in sorted(REQUIRED_CAMERA0_DUTIES, reverse=(block_id % 2 == 0)):
            for pulse_index in range(pulses_per_duty // 3):
                rows.append(
                    {
                        "campaign_id": "camera0-intensity-threshold-statistics",
                        "camera_index": 0,
                        "duty": duty,
                        "pulse_index": pulse_index,
                        "block_id": block_id,
                        "block_order": pulse_index,
                        "is_dark_control": duty == 0,
                        "is_positive_control": duty in {16, 24, 32, 48, 64, 128},
                    }
                )
    return rows


def test_validate_camera0_plan_rows_accepts_complete_plan_with_fixed_60_and_blocks():
    plan_rows = _build_plan()
    report = validate_camera0_plan_rows(plan_rows)

    assert report["is_compliant"] is True
    assert report["missing_duties"] == []
    assert report["under_replicated_duties"] == []
    assert report["pulses_per_duty_target"] == FIXED_PULSES_PER_DUTY
    assert report["has_interleaved_blocks"] is True
    assert report["required_plan_columns"] == list(REQUIRED_CAMERA0_PLAN_COLUMNS)


def test_validate_camera0_plan_rows_rejects_missing_duty_and_under_replicated():
    plan_rows = [row for row in _build_plan(pulses_per_duty=30) if row["duty"] != 12]
    report = validate_camera0_plan_rows(plan_rows)

    assert report["is_compliant"] is False
    assert 12 in report["missing_duties"]
    assert report["under_replicated_duties"] == [12]
