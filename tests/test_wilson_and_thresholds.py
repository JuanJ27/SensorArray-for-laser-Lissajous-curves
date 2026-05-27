from analysis.uncertainty import (
    bootstrap_threshold_estimates,
    estimate_detection_thresholds,
    wilson_interval,
)


def test_wilson_interval_bounds_are_valid_and_ordered():
    low, high = wilson_interval(18, 60)

    assert 0.0 <= low <= high <= 1.0
    assert low < high


def test_estimate_detection_thresholds_are_monotonic():
    by_duty_counts = [
        {"duty": 0, "detected": 0, "total": 60},
        {"duty": 4, "detected": 5, "total": 60},
        {"duty": 6, "detected": 25, "total": 60},
        {"duty": 8, "detected": 44, "total": 60},
        {"duty": 10, "detected": 54, "total": 60},
        {"duty": 12, "detected": 58, "total": 60},
    ]

    thresholds = estimate_detection_thresholds(by_duty_counts)

    assert thresholds["duty50"] <= thresholds["duty90"] <= thresholds["duty95"]


def test_bootstrap_thresholds_are_reproducible_with_seed():
    by_duty_counts = [
        {"duty": 0, "detected": 0, "total": 60},
        {"duty": 4, "detected": 5, "total": 60},
        {"duty": 6, "detected": 25, "total": 60},
        {"duty": 8, "detected": 44, "total": 60},
        {"duty": 10, "detected": 54, "total": 60},
        {"duty": 12, "detected": 58, "total": 60},
    ]

    first = bootstrap_threshold_estimates(by_duty_counts, n_bootstrap=200, seed=7)
    second = bootstrap_threshold_estimates(by_duty_counts, n_bootstrap=200, seed=7)

    assert first == second
    assert first["duty50"]["low"] <= first["duty50"]["mid"] <= first["duty50"]["high"]
    assert first["duty90"]["low"] <= first["duty90"]["mid"] <= first["duty90"]["high"]
    assert first["duty95"]["low"] <= first["duty95"]["mid"] <= first["duty95"]["high"]
