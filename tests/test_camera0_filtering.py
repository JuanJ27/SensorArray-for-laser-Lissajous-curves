from analysis.aggregate import filter_camera0_campaign_rows


def test_filter_camera0_campaign_rows_keeps_only_camera0_campaign_rows():
    rows = [
        {
            "run_id": "ok-1",
            "campaign_id": "camera0-intensity-threshold-statistics",
            "camera_index": 0,
            "acquisition_fingerprint": "fps30-exp120",
        },
        {
            "run_id": "wrong-camera",
            "campaign_id": "camera0-intensity-threshold-statistics",
            "camera_index": 2,
            "acquisition_fingerprint": "fps30-exp120",
        },
        {
            "run_id": "legacy",
            "campaign_id": "legacy-campaign",
            "camera_index": 0,
            "acquisition_fingerprint": "fps30-exp120",
        },
    ]

    accepted, excluded = filter_camera0_campaign_rows(rows, "camera0-intensity-threshold-statistics")

    assert len(accepted) == 1
    assert accepted[0]["run_id"] == "ok-1"
    reasons = {row["exclusion_reason"] for row in excluded}
    assert "wrong_camera_index" in reasons
    assert "campaign_mismatch" in reasons


def test_filter_camera0_campaign_rows_excludes_missing_metadata_and_drift():
    rows = [
        {
            "run_id": "missing",
            "camera_index": 0,
            "acquisition_fingerprint": "fps30-exp120",
        },
        {
            "run_id": "drift",
            "campaign_id": "camera0-intensity-threshold-statistics",
            "camera_index": 0,
            "acquisition_fingerprint": "fps60-exp60",
        },
        {
            "run_id": "anchor",
            "campaign_id": "camera0-intensity-threshold-statistics",
            "camera_index": 0,
            "acquisition_fingerprint": "fps30-exp120",
        },
        {
            "run_id": "anchor-2",
            "campaign_id": "camera0-intensity-threshold-statistics",
            "camera_index": 0,
            "acquisition_fingerprint": "fps30-exp120",
        },
    ]

    accepted, excluded = filter_camera0_campaign_rows(rows, "camera0-intensity-threshold-statistics")

    assert len(accepted) == 2
    assert accepted[0]["run_id"] == "anchor"
    assert accepted[1]["run_id"] == "anchor-2"
    excluded_map = {row["run_id"]: row["exclusion_reason"] for row in excluded}
    assert excluded_map["missing"] == "missing_campaign_id"
    assert excluded_map["drift"] == "acquisition_fingerprint_drift"
