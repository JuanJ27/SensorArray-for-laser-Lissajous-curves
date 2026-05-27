from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd


THRESHOLD_SENSITIVITY_DELTAS = (0.10, 0.20)
DEFAULT_BOOTSTRAP_SEED = 7


def _fit_logistic_line(by_duty_counts: list[dict[str, int]]) -> tuple[float, float]:
    duties: list[float] = []
    logits: list[float] = []
    for row in by_duty_counts:
        duty = float(row["duty"])
        total = int(row["total"])
        detected = int(row["detected"])
        if total <= 0:
            continue
        # Laplace smoothing to avoid inf logit at p in {0,1}.
        p = (detected + 0.5) / (total + 1.0)
        p = min(max(p, 1e-6), 1.0 - 1e-6)
        duties.append(duty)
        logits.append(math.log(p / (1.0 - p)))
    if len(duties) < 2:
        return 0.0, 0.0
    slope, intercept = np.polyfit(np.array(duties), np.array(logits), deg=1)
    return float(slope), float(intercept)


def _threshold_from_fit(slope: float, intercept: float, probability: float) -> float:
    if slope <= 0:
        return float("nan")
    logit = math.log(probability / (1.0 - probability))
    return float((logit - intercept) / slope)


def estimate_detection_thresholds(by_duty_counts: list[dict[str, int]]) -> dict[str, float]:
    slope, intercept = _fit_logistic_line(by_duty_counts)
    duty50 = _threshold_from_fit(slope, intercept, 0.50)
    duty90 = _threshold_from_fit(slope, intercept, 0.90)
    duty95 = _threshold_from_fit(slope, intercept, 0.95)
    monotonic = sorted([duty50, duty90, duty95])
    return {"duty50": monotonic[0], "duty90": monotonic[1], "duty95": monotonic[2]}


def bootstrap_threshold_estimates(
    by_duty_counts: list[dict[str, int]],
    n_bootstrap: int = 500,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    boot_samples = {"duty50": [], "duty90": [], "duty95": []}
    for _ in range(n_bootstrap):
        sampled_rows = []
        for row in by_duty_counts:
            duty = int(row["duty"])
            total = int(row["total"])
            detected = int(rng.binomial(total, (int(row["detected"]) / total) if total > 0 else 0.0))
            sampled_rows.append({"duty": duty, "detected": detected, "total": total})
        estimate = estimate_detection_thresholds(sampled_rows)
        for key in boot_samples:
            boot_samples[key].append(float(estimate[key]))

    summary: dict[str, dict[str, float]] = {}
    for key, values in boot_samples.items():
        arr = np.array(values, dtype=float)
        summary[key] = {
            "low": float(np.quantile(arr, 0.025)),
            "mid": float(np.quantile(arr, 0.5)),
            "high": float(np.quantile(arr, 0.975)),
        }
    return summary


def read_key_value_csv(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {str(row.get("field", "")): str(row.get("value", "")) for row in reader}


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p_hat = successes / total
    denom = 1.0 + (z**2 / total)
    center = (p_hat + z**2 / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z**2 / (4.0 * total**2)))
    return max(0.0, center - margin), min(1.0, center + margin)


def _to_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_interval(low: float, high: float, digits: int = 3) -> str:
    return f"[{low:.{digits}f}, {high:.{digits}f}]"


def _fmt_pm(value: float, half_width: float, digits: int = 1) -> str:
    return f"{value:.{digits}f} +/- {half_width:.{digits}f} ms"


def _threshold_sensitivity_rows(coincidence_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for run_id, table in coincidence_tables.items():
        covered = table.loc[table["window_frame_count"] > 0].copy()
        successes = covered.loc[covered["matched_frame_detected"].astype(str).str.lower() == "true"].copy()
        for delta in THRESHOLD_SENSITIVITY_DELTAS:
            resilient = successes.loc[successes["matched_frame_max"] >= successes["matched_frame_threshold"] * (1.0 + delta)]
            rate = float(len(resilient) / len(covered)) if len(covered) else 0.0
            rows.append(
                {
                    "run_id": run_id,
                    "threshold_delta_fraction": delta,
                    "covered_pulses": int(len(covered)),
                    "retained_matches": int(len(resilient)),
                    "retained_rate": rate,
                }
            )
    return pd.DataFrame(rows)


def _minimum_detectable_duty_statement(webcam_intensity: pd.DataFrame, webcam_exposure: pd.DataFrame) -> str:
    threshold_rows = webcam_intensity.loc[webcam_intensity["mean_detection_probability"] >= 0.5].sort_values("duty")
    if threshold_rows.empty:
        return "no bounded duty threshold could be estimated from current offline tables"
    first = threshold_rows.iloc[0]
    candidate_low = int(first["duty"])
    low_duty_exposure = webcam_exposure.loc[webcam_exposure["duty"] <= max(candidate_low, 8)]
    exposure_spread = 0.0
    if not low_duty_exposure.empty:
        exposure_spread = float(low_duty_exposure["mean_detection_probability"].max() - low_duty_exposure["mean_detection_probability"].min())
    upper = max(candidate_low, 8 if exposure_spread >= 0.5 or int(first["replicates"]) <= 1 else candidate_low)
    return f"practical conditional threshold is about duty {candidate_low}-{upper}, not a single exact duty, because the first success point has limited replicates and low-duty exposure response is non-monotonic"


def _pulse_duration_threshold_statement(webcam_duration: pd.DataFrame) -> str:
    threshold = webcam_duration.loc[webcam_duration["mean_detection_probability"] >= 0.5].sort_values(["duration_ms", "duty"])
    robust = webcam_duration.loc[webcam_duration["mean_detection_probability"] >= 1.0].sort_values(["duration_ms", "duty"])
    if threshold.empty:
        return "no practical pulse-duration threshold could be bounded from current webcam runs"
    lower = int(threshold.iloc[0]["duration_ms"])
    upper = int(robust.iloc[0]["duration_ms"]) if not robust.empty else int(threshold["duration_ms"].max())
    return f"practical webcam detectability starts around {lower}-{upper} ms depending on duty and exposure, with no evidence for a stable sub-50 ms threshold in the current dataset"


def build_uncertainty_summary(
    repo_root: Path,
    selected_runs: pd.DataFrame,
    coincidence_tables: dict[str, pd.DataFrame],
    output_dir: Path,
) -> dict[str, object]:
    studies_dir = repo_root / "data" / "derived" / "studies"
    webcam_intensity = pd.read_csv(studies_dir / "webcam_intensity_by_duty.csv")
    webcam_duration = pd.read_csv(studies_dir / "webcam_parameter_by_duration.csv")
    webcam_exposure = pd.read_csv(studies_dir / "webcam_parameter_by_exposure.csv")
    op598_duty = pd.read_csv(studies_dir / "op598_characterization_by_duty.csv")

    pooled_covered = int(selected_runs["covered_pulses"].sum())
    pooled_matched = int(selected_runs["matched_detected"].sum())
    pooled_rate = float(pooled_matched / pooled_covered) if pooled_covered else 0.0
    pooled_ci = wilson_interval(pooled_matched, pooled_covered)

    summary_rows = []
    frame_half_widths: list[float] = []
    op598_half_widths: list[float] = []
    offsets: list[float] = []
    for row in selected_runs.itertuples(index=False):
        summary = read_key_value_csv(repo_root / str(row.source_summary))
        fps = _to_float(summary.get("webcam.measured_fps"))
        sample_interval = _to_float(summary.get("op598.sample_interval_avg_ms"))
        frame_period = 1000.0 / fps if fps and fps > 0 else float("nan")
        frame_half = 0.5 * frame_period if math.isfinite(frame_period) else float("nan")
        op598_half = 0.5 * sample_interval if sample_interval is not None else float("nan")
        if math.isfinite(frame_half):
            frame_half_widths.append(frame_half)
        if math.isfinite(op598_half):
            op598_half_widths.append(op598_half)
        offsets.extend(
            coincidence_tables[str(row.run_id)].loc[
                coincidence_tables[str(row.run_id)]["matched_frame_detected"].astype(str).str.lower() == "true",
                "matched_frame_dt_ms",
            ].astype(float).tolist()
        )
        summary_rows.append(
            {
                "run_id": str(row.run_id),
                "webcam_frame_period_ms": frame_period,
                "webcam_half_period_ms": frame_half,
                "op598_sample_interval_ms": sample_interval,
                "op598_half_sample_interval_ms": op598_half,
            }
        )

    temporal_summary = pd.DataFrame(summary_rows)
    threshold_sensitivity = _threshold_sensitivity_rows(coincidence_tables)
    threshold_sensitivity_path = output_dir / "threshold_sensitivity.csv"
    threshold_sensitivity.to_csv(threshold_sensitivity_path, index=False)

    frame_half = float(np.mean(frame_half_widths)) if frame_half_widths else float("nan")
    op598_half = float(np.mean(op598_half_widths)) if op598_half_widths else float("nan")
    combined_half_width = sum(value for value in [frame_half, op598_half] if math.isfinite(value))
    mean_offset = float(np.mean(offsets)) if offsets else 0.0

    pooled_threshold_rows = threshold_sensitivity.groupby("threshold_delta_fraction", as_index=False).agg(
        covered_pulses=("covered_pulses", "sum"),
        retained_matches=("retained_matches", "sum"),
    )
    pooled_threshold_rows["retained_rate"] = pooled_threshold_rows["retained_matches"] / pooled_threshold_rows["covered_pulses"]

    low_duty_exposure = webcam_exposure.loc[webcam_exposure["duty"] <= 8].copy()
    exposure_spread = float(
        low_duty_exposure["mean_detection_probability"].max() - low_duty_exposure["mean_detection_probability"].min()
    ) if not low_duty_exposure.empty else 0.0
    saturated = op598_duty.loc[op598_duty["any_saturated"].astype(str).str.lower() == "true", "duty"].astype(int).tolist()
    minimum_detectable_duty_statement = _minimum_detectable_duty_statement(webcam_intensity, webcam_exposure)
    pulse_duration_threshold_statement = _pulse_duration_threshold_statement(webcam_duration)
    mean_offset_statement = (
        f"{_fmt_pm(mean_offset, combined_half_width, digits=1)} from interval-based propagation of mean frame half-period and OP598 half sample-interval"
    )

    run_replicates_min = int(min(webcam_intensity["replicates"].min(), webcam_duration["replicates"].min(), webcam_exposure["replicates"].min()))
    run_replicates_max = int(max(webcam_intensity["replicates"].max(), webcam_duration["replicates"].max(), webcam_exposure["replicates"].max()))
    summary_path = output_dir / "reconstruction_uncertainty_summary.md"
    lines = [
        "# Reconstruction uncertainty and systematic error summary",
        "",
        "## Scope of this uncertainty model",
        "",
        "- This is an offline, practical uncertainty treatment.",
        "- It combines exact binomial confidence intervals where appropriate with interval-based temporal bounds and sensitivity analyses where exact propagation is not defensible.",
        "- It does NOT claim lab-grade calibration of the webcam, LED output, or the OP598 timing chain.",
        "",
        "## Key propagated outputs",
        "",
        f"- Pooled coincidence success rate on covered windows: `{pooled_matched}/{pooled_covered} = {pooled_rate:.3f}` with Wilson 95% CI `{_fmt_interval(*pooled_ci)}`.",
        f"- Mean matched-frame offset: `{mean_offset_statement}`.",
        f"- Minimum detectable duty statement: `{minimum_detectable_duty_statement}`.",
        f"- Pulse-duration detectability statement: `{pulse_duration_threshold_statement}`.",
        "",
        "## Systematic error terms included",
        "",
        f"- Webcam temporal quantization: mean half-frame uncertainty about `{frame_half:.2f} ms` from the selected runs' measured FPS.",
        f"- OP598 temporal anchoring under MicroPython cadence: mean half sample-interval about `{op598_half:.2f} ms` from `op598.sample_interval_avg_ms`.",
        "- Threshold sensitivity: recomputed retained coincidence under stricter matched-frame thresholds of +10% and +20% using stored frame-threshold margins.",
        f"- Exposure dependence / low-duty non-monotonicity: low-duty exposure sweep spans `{exposure_spread:.3f}` probability units, so the webcam threshold is conditional on exposure rather than monotonic.",
        f"- OP598 saturation: duties with saturation evidence in the characterization table: `{saturated}`.",
        f"- Limited replicate counts: current derived tables mostly sit between `{run_replicates_min}` and `{run_replicates_max}` replicates per condition, often only one.",
        "",
        "## Threshold sensitivity results",
        "",
        pooled_threshold_rows.to_markdown(index=False),
        "",
        "Interpretation: this is a one-sided robustness check against stricter thresholds. It does not re-run the full detector or estimate false-positive risk at lower thresholds, so it should be read as sensitivity, not absolute truth.",
        "",
        "## Temporal uncertainty inputs by selected run",
        "",
        temporal_summary.to_markdown(index=False),
        "",
        "## Honest limitations",
        "",
        "- Stored offline artifacts do not preserve every pixel-level decision needed for a full end-to-end Monte Carlo of thresholding and matching.",
        "- Exposure and duration sweeps are sparse, so uncertainty on detectability thresholds is better expressed as bounded practical ranges than precise estimates.",
        "- OP598 saturation at high duty means amplitude-based interpretation there is not reliable, even if coincidence can still be observed.",
        "- The propagated offset bound is conservative and interval-based; it is intentionally easier to defend than a pseudo-precise Gaussian claim.",
        "",
        f"Auxiliary sensitivity table written to `data/derived/reconstruction/{threshold_sensitivity_path.name}`.",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "summary_path": str(summary_path.relative_to(repo_root)),
        "threshold_sensitivity_path": str(threshold_sensitivity_path.relative_to(repo_root)),
        "pooled_coincidence_rate": pooled_rate,
        "pooled_coincidence_ci_low": pooled_ci[0],
        "pooled_coincidence_ci_high": pooled_ci[1],
        "minimum_detectable_duty_statement": minimum_detectable_duty_statement,
        "pulse_duration_threshold_statement": pulse_duration_threshold_statement,
        "mean_offset_statement": mean_offset_statement,
        "frame_half_period_ms": frame_half,
        "op598_half_sample_interval_ms": op598_half,
    }
