from __future__ import annotations

import math
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from .uncertainty import build_uncertainty_summary, read_key_value_csv, wilson_interval


DEFAULT_SELECTION_LIMIT = 3
DEFAULT_PHASE_OFFSETS = (-2, -1, 0, 1, 2)
PHASE_LABELS = {
    -2: "before",
    -1: "approach",
    0: "hit",
    1: "decay",
    2: "after",
}
PULSE_STRIP_OFFSETS = (-1, 0, 1)
PULSE_STRIP_PULSES_PER_RUN = 3
COMPARISON_GROUP_ORDER = ("pooled",)


@dataclass(frozen=True)
class ReconstructionPulse:
    run_id: str
    variant: str
    pulse_index: int
    matched_frame_index: int
    matched_frame_dt_ms: float


def find_repo_root(start: Path | None = None) -> Path:
    candidates = [start.resolve() if start else Path.cwd().resolve(), Path(__file__).resolve().parent]
    for candidate in candidates:
        for parent in [candidate, *candidate.parents]:
            if (parent / ".git").exists() and (parent / "data" / "derived" / "studies").exists():
                return parent
    raise FileNotFoundError("No se pudo ubicar la raiz del repo para la reconstruccion.")


def reconstruction_dir(repo_root: Path) -> Path:
    path = repo_root / "data" / "derived" / "reconstruction"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _phase_label(offset: int) -> str:
    return PHASE_LABELS.get(offset, f"offset_{offset:+d}")


def _grayscale(array: np.ndarray) -> np.ndarray:
    return np.mean(array.astype(np.float32), axis=2)


def _normalize_preview(array: np.ndarray) -> np.ndarray:
    gray = _grayscale(array)
    low = float(np.percentile(gray, 2.0))
    high = float(np.percentile(gray, 99.0))
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        normalized = np.clip(gray, 0, 255)
    else:
        normalized = np.clip((gray - low) * (255.0 / (high - low)), 0, 255)
    rgb = np.repeat(normalized[:, :, None], 3, axis=2)
    return rgb.astype(np.uint8)


def load_dual_runs(repo_root: Path) -> pd.DataFrame:
    path = repo_root / "data" / "derived" / "studies" / "dual_random_train_runs.csv"
    if not path.exists():
        raise FileNotFoundError(f"Falta la tabla de corridas duales: {path}")
    return pd.read_csv(path)


def rank_dual_runs(dual_runs: pd.DataFrame, selection_limit: int = DEFAULT_SELECTION_LIMIT) -> pd.DataFrame:
    ranked = dual_runs.copy()
    ranked["limited_coverage_flag"] = ranked["limited_coverage"].astype(str).str.lower() == "true"
    ranked["variant_priority"] = np.where(
        ranked["variant"].eq("phase2_statistical_reconstruction_matrix"),
        0,
        1,
    )
    ranked["run_timestamp"] = ranked["run_id"].str.replace("random-train_", "", regex=False).astype(int)
    ranked["eligible_for_reconstruction"] = (
        ~ranked["limited_coverage_flag"]
        & (ranked["matched_detected"] > 0)
        & (ranked["coincidence_success_rate_windowed"] > 0)
    )

    ranked = ranked.sort_values(
        [
            "eligible_for_reconstruction",
            "coincidence_success_rate_windowed",
            "matched_detected",
            "covered_pulses",
            "variant_priority",
            "run_timestamp",
        ],
        ascending=[False, False, False, False, True, False],
    ).reset_index(drop=True)

    ranked["selected_for_reconstruction"] = False
    selected_indexes = ranked.index[ranked["eligible_for_reconstruction"]].tolist()[:selection_limit]
    ranked.loc[selected_indexes, "selected_for_reconstruction"] = True
    ranked["selection_rank"] = ""
    ranked.loc[selected_indexes, "selection_rank"] = [str(index + 1) for index in range(len(selected_indexes))]

    def describe_selection(row: pd.Series) -> str:
        parts = []
        if not row["limited_coverage_flag"]:
            parts.append("full_video_coverage")
        if float(row["coincidence_success_rate_windowed"]) >= 1.0:
            parts.append("perfect_windowed_coincidence")
        if row["variant"] == "phase2_statistical_reconstruction_matrix":
            parts.append("matrix_variant")
        if int(row["matched_detected"]) >= 10:
            parts.append("10_matched_pulses")
        if bool(row["selected_for_reconstruction"]):
            parts.append("selected_for_aggregate")
        return ";".join(parts)

    ranked["selection_reason"] = ranked.apply(describe_selection, axis=1)
    return ranked.drop(columns=["limited_coverage_flag", "variant_priority", "run_timestamp"])


def load_selected_pulses(
    repo_root: Path,
    ranked_runs: pd.DataFrame,
) -> tuple[pd.DataFrame, list[ReconstructionPulse], dict[str, pd.DataFrame]]:
    selected_runs = ranked_runs.loc[ranked_runs["selected_for_reconstruction"]].copy()
    if selected_runs.empty:
        raise RuntimeError("No hay corridas duales elegibles para la reconstruccion estadistica.")

    coincidence_tables: dict[str, pd.DataFrame] = {}
    pulses: list[ReconstructionPulse] = []
    for run in selected_runs.itertuples(index=False):
        coincidence_path = repo_root / str(run.source_coincidence)
        table = pd.read_csv(coincidence_path)
        coincidence_tables[str(run.run_id)] = table
        matched = table.loc[
            (table["matched_frame_index"] >= 0)
            & (table["matched_frame_detected"].astype(str).str.lower() == "true")
        ].copy()
        for row in matched.itertuples(index=False):
            pulses.append(
                ReconstructionPulse(
                    run_id=str(run.run_id),
                    variant=str(run.variant),
                    pulse_index=int(row.pulse_index),
                    matched_frame_index=int(row.matched_frame_index),
                    matched_frame_dt_ms=float(row.matched_frame_dt_ms),
                )
            )
    if not pulses:
        raise RuntimeError("Las corridas seleccionadas no aportan pulsos emparejados detectados.")
    return selected_runs, pulses, coincidence_tables


def _extract_frames(video_path: Path, frame_indexes: list[int]) -> dict[int, np.ndarray]:
    unique_indexes = sorted({index for index in frame_indexes if index >= 0})
    if not unique_indexes:
        return {}
    if not video_path.exists():
        raise FileNotFoundError(f"Falta el video requerido para extraer frames: {video_path}")

    expression = "+".join(f"eq(n\\,{index})" for index in unique_indexes)
    with tempfile.TemporaryDirectory(prefix="reconstruction_frames_") as temp_dir:
        output_pattern = Path(temp_dir) / "frame_%06d.png"
        command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"select={expression}",
            "-vsync",
            "0",
            str(output_pattern),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "ffmpeg no pudo extraer los frames requeridos.")

        extracted_paths = sorted(Path(temp_dir).glob("frame_*.png"))
        if len(extracted_paths) != len(unique_indexes):
            raise RuntimeError(
                "ffmpeg no devolvio la misma cantidad de frames solicitados: "
                f"pedidos={len(unique_indexes)} obtenidos={len(extracted_paths)}"
            )

        frames: dict[int, np.ndarray] = {}
        for frame_index, extracted_path in zip(unique_indexes, extracted_paths, strict=True):
            with Image.open(extracted_path) as image:
                frames[frame_index] = np.array(image.convert("RGB"), dtype=np.uint8)
        return frames


def extract_run_frames(
    repo_root: Path,
    selected_runs: pd.DataFrame,
    pulses: list[ReconstructionPulse],
    offsets: tuple[int, ...] = DEFAULT_PHASE_OFFSETS,
) -> dict[str, dict[int, np.ndarray]]:
    requested_by_run: dict[str, set[int]] = {}
    for pulse in pulses:
        requested = requested_by_run.setdefault(pulse.run_id, set())
        for offset in offsets:
            requested.add(max(0, pulse.matched_frame_index + offset))

    frames_by_run: dict[str, dict[int, np.ndarray]] = {}
    for run in selected_runs.itertuples(index=False):
        video_path = repo_root / Path(str(run.source_summary)).parent / "webcam_capture.avi"
        frames_by_run[str(run.run_id)] = _extract_frames(video_path, sorted(requested_by_run.get(str(run.run_id), set())))
    return frames_by_run


def _stack_average(frames: list[np.ndarray]) -> np.ndarray:
    reference_height, reference_width = frames[0].shape[:2]
    normalized: list[np.ndarray] = []
    for frame in frames:
        if frame.shape[:2] != (reference_height, reference_width):
            pil_frame = Image.fromarray(frame).resize((reference_width, reference_height), Image.Resampling.BILINEAR)
            normalized.append(np.array(pil_frame, dtype=np.float32))
        else:
            normalized.append(frame.astype(np.float32))
    averaged = np.mean(np.stack(normalized, axis=0), axis=0)
    return np.clip(averaged, 0, 255).astype(np.uint8)


def _save_rgb(path: Path, array: np.ndarray) -> None:
    Image.fromarray(array.astype(np.uint8), mode="RGB").save(path)


def _label_image(array: np.ndarray, text: str) -> Image.Image:
    image = Image.fromarray(array.astype(np.uint8), mode="RGB")
    lines = text.splitlines()
    banner_height = 14 + 16 * max(1, len(lines))
    canvas = Image.new("RGB", (image.width, image.height + banner_height), color=(14, 14, 18))
    canvas.paste(image, (0, banner_height))
    draw = ImageDraw.Draw(canvas)
    for index, line in enumerate(lines):
        draw.text((8, 6 + index * 16), line, fill=(245, 245, 245))
    return canvas


def _text_tile(width: int, height: int, title: str, lines: list[str]) -> Image.Image:
    canvas = Image.new("RGB", (width, height), color=(22, 22, 28))
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 8), title, fill=(250, 250, 250))
    for index, line in enumerate(lines):
        draw.text((10, 32 + index * 16), line, fill=(220, 220, 220))
    return canvas


def _concat_horizontal(images: list[Image.Image], gap: int = 4) -> Image.Image:
    width = sum(image.width for image in images) + gap * max(0, len(images) - 1)
    height = max(image.height for image in images)
    canvas = Image.new("RGB", (width, height), color=(10, 10, 10))
    x = 0
    for image in images:
        canvas.paste(image, (x, 0))
        x += image.width + gap
    return canvas


def _concat_vertical(images: list[Image.Image], gap: int = 6) -> Image.Image:
    width = max(image.width for image in images)
    height = sum(image.height for image in images) + gap * max(0, len(images) - 1)
    canvas = Image.new("RGB", (width, height), color=(10, 10, 10))
    y = 0
    for image in images:
        canvas.paste(image, (0, y))
        y += image.height + gap
    return canvas


def _group_effective_sample_size(group_counts: dict[str, int]) -> float:
    weights = np.array([count for count in group_counts.values() if count > 0], dtype=float)
    if len(weights) == 0:
        return 0.0
    return float((weights.sum() ** 2) / np.square(weights).sum())


def _run_group_summary(selected_runs: pd.DataFrame) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    for row in selected_runs.itertuples(index=False):
        success_low, success_high = wilson_interval(int(row.matched_detected), int(row.covered_pulses))
        summary_path = Path(str(row.source_summary))
        summaries[str(row.run_id)] = {
            "run_id": str(row.run_id),
            "variant": str(row.variant),
            "covered_pulses": int(row.covered_pulses),
            "matched_detected": int(row.matched_detected),
            "coverage_fraction": float(row.coverage_fraction),
            "coincidence_success_rate_windowed": float(row.coincidence_success_rate_windowed),
            "coincidence_success_ci_low": success_low,
            "coincidence_success_ci_high": success_high,
            "mean_offset_ms_detected": float(row.mean_offset_ms_detected),
            "source_summary": summary_path,
        }
    return summaries


def _build_phase_rows(
    repo_root: Path,
    output_dir: Path,
    selected_runs: pd.DataFrame,
    pulses: list[ReconstructionPulse],
    frames_by_run: dict[str, dict[int, np.ndarray]],
    coincidence_tables: dict[str, pd.DataFrame],
    phase_offsets: tuple[int, ...],
) -> tuple[pd.DataFrame, dict[str, str]]:
    phase_dir = output_dir / "phase_averages"
    phase_dir.mkdir(parents=True, exist_ok=True)
    pulse_counts_by_run: dict[str, int] = {str(run_id): 0 for run_id in selected_runs["run_id"].tolist()}
    for pulse in pulses:
        pulse_counts_by_run[pulse.run_id] = pulse_counts_by_run.get(pulse.run_id, 0) + 1

    phase_frames_by_group: dict[str, dict[int, list[np.ndarray]]] = {
        "pooled": {offset: [] for offset in phase_offsets},
    }
    offset_samples_by_group: dict[str, list[float]] = {"pooled": []}
    for run_id in selected_runs["run_id"].tolist():
        phase_frames_by_group[str(run_id)] = {offset: [] for offset in phase_offsets}
        offset_samples_by_group[str(run_id)] = []

    for pulse in pulses:
        run_frames = frames_by_run[pulse.run_id]
        offset_samples_by_group["pooled"].append(float(pulse.matched_frame_dt_ms))
        offset_samples_by_group[pulse.run_id].append(float(pulse.matched_frame_dt_ms))
        for offset in phase_offsets:
            frame = run_frames.get(max(0, pulse.matched_frame_index + offset))
            if frame is None:
                continue
            phase_frames_by_group["pooled"][offset].append(frame)
            phase_frames_by_group[pulse.run_id][offset].append(frame)

    run_summaries = _run_group_summary(selected_runs)
    pooled_covered = int(selected_runs["covered_pulses"].sum())
    pooled_matched = int(selected_runs["matched_detected"].sum())
    pooled_low, pooled_high = wilson_interval(pooled_matched, pooled_covered)
    pooled_rate = float(pooled_matched / pooled_covered) if pooled_covered else 0.0
    pooled_coverage = float(selected_runs["covered_pulses"].sum() / selected_runs["pulse_count_table"].sum())
    group_summaries: dict[str, dict[str, object]] = {
        "pooled": {
            "run_id": "pooled",
            "variant": "selected_runs_pool",
            "covered_pulses": pooled_covered,
            "matched_detected": pooled_matched,
            "coverage_fraction": pooled_coverage,
            "coincidence_success_rate_windowed": pooled_rate,
            "coincidence_success_ci_low": pooled_low,
            "coincidence_success_ci_high": pooled_high,
            "mean_offset_ms_detected": float(np.mean(offset_samples_by_group["pooled"])) if offset_samples_by_group["pooled"] else float("nan"),
            "source_summary": Path(""),
        },
        **run_summaries,
    }
    pooled_effective_n = _group_effective_sample_size(pulse_counts_by_run)

    phase_rows: list[dict[str, object]] = []
    preview_paths: dict[str, str] = {}
    for group_id, phase_map in phase_frames_by_group.items():
        group_dir = phase_dir / group_id
        group_dir.mkdir(parents=True, exist_ok=True)
        before_average = None
        if phase_map.get(-2):
            before_average = _stack_average(phase_map[-2])
        offsets = offset_samples_by_group.get(group_id, [])
        offset_std = float(np.std(offsets, ddof=1)) if len(offsets) > 1 else 0.0
        group_summary = group_summaries[group_id]
        effective_n = pooled_effective_n if group_id == "pooled" else float(len(offsets))

        for offset in phase_offsets:
            frames = phase_map[offset]
            if not frames:
                continue
            average = _stack_average(frames)
            preview = _normalize_preview(average)
            preview_path = group_dir / f"phase_{offset:+d}_{_phase_label(offset)}.png"
            _save_rgb(preview_path, preview)
            preview_paths[f"{group_id}:{offset}"] = _display_path(preview_path, repo_root)
            gray = _grayscale(average)
            diff_mean = 0.0
            diff_abs_mean = 0.0
            positive_fraction = 0.0
            if before_average is not None:
                before_gray = _grayscale(before_average)
                diff = gray - before_gray
                diff_mean = float(np.mean(diff))
                diff_abs_mean = float(np.mean(np.abs(diff)))
                positive_fraction = float(np.mean(diff > 0.0))

            phase_rows.append(
                {
                    "group_type": "pooled" if group_id == "pooled" else "run",
                    "group_id": group_id,
                    "run_id": "" if group_id == "pooled" else group_id,
                    "variant": str(group_summary["variant"]),
                    "phase_offset": offset,
                    "phase_label": _phase_label(offset),
                    "frame_count": len(frames),
                    "matched_pulses": int(group_summary["matched_detected"]),
                    "effective_sample_size": round(effective_n, 6),
                    "covered_pulses": int(group_summary["covered_pulses"]),
                    "coverage_fraction": round(float(group_summary["coverage_fraction"]), 6),
                    "coincidence_success_rate_windowed": round(float(group_summary["coincidence_success_rate_windowed"]), 6),
                    "coincidence_success_ci_low": round(float(group_summary["coincidence_success_ci_low"]), 6),
                    "coincidence_success_ci_high": round(float(group_summary["coincidence_success_ci_high"]), 6),
                    "mean_offset_ms_detected": round(float(group_summary["mean_offset_ms_detected"]), 6),
                    "offset_std_ms_detected": round(offset_std, 6),
                    "frame_mean_gray": round(float(np.mean(gray)), 6),
                    "frame_p95_gray": round(float(np.percentile(gray, 95.0)), 6),
                    "delta_mean_gray_vs_before": round(diff_mean, 6),
                    "delta_abs_mean_gray_vs_before": round(diff_abs_mean, 6),
                    "positive_delta_fraction_vs_before": round(positive_fraction, 6),
                    "preview_path": _display_path(preview_path, repo_root),
                }
            )

    statistics = pd.DataFrame(phase_rows).sort_values(["group_type", "group_id", "phase_offset"]).reset_index(drop=True)
    return statistics, preview_paths


def _build_avg_and_heatmap(
    repo_root: Path,
    output_dir: Path,
    pulses: list[ReconstructionPulse],
    frames_by_run: dict[str, dict[int, np.ndarray]],
) -> dict[str, str]:
    matched_frames: list[np.ndarray] = []
    delta_frames: list[np.ndarray] = []
    for pulse in pulses:
        run_frames = frames_by_run[pulse.run_id]
        matched_frame = run_frames.get(pulse.matched_frame_index)
        before_frame = run_frames.get(max(0, pulse.matched_frame_index - 1))
        if matched_frame is not None:
            matched_frames.append(matched_frame)
        if matched_frame is not None and before_frame is not None:
            delta_frames.append(np.maximum(matched_frame.astype(np.int16) - before_frame.astype(np.int16), 0).astype(np.uint8))

    if not matched_frames:
        raise RuntimeError("No se pudieron recuperar frames emparejados para la reconstruccion.")

    avg_flash_frame = _stack_average(matched_frames)
    avg_flash_frame_path = output_dir / "avg_flash_frame.png"
    _save_rgb(avg_flash_frame_path, avg_flash_frame)

    if delta_frames:
        delta_average = _stack_average(delta_frames).astype(np.float32) / 255.0
        heatmap_rgba = cm.get_cmap("magma")(delta_average.mean(axis=2))
        heatmap_rgb = np.clip(heatmap_rgba[:, :, :3] * 255.0, 0, 255).astype(np.uint8)
    else:
        gray = np.mean(avg_flash_frame.astype(np.float32), axis=2)
        normalized = gray / max(float(gray.max()), 1.0)
        heatmap_rgba = cm.get_cmap("magma")(normalized)
        heatmap_rgb = np.clip(heatmap_rgba[:, :, :3] * 255.0, 0, 255).astype(np.uint8)
    heatmap_path = output_dir / "flash_heatmap.png"
    _save_rgb(heatmap_path, heatmap_rgb)
    return {
        "avg_flash_frame": _display_path(avg_flash_frame_path, repo_root),
        "flash_heatmap": _display_path(heatmap_path, repo_root),
    }


def _build_slowmo_and_pulse_strips(
    repo_root: Path,
    output_dir: Path,
    selected_runs: pd.DataFrame,
    pulses: list[ReconstructionPulse],
    frames_by_run: dict[str, dict[int, np.ndarray]],
    phase_offsets: tuple[int, ...],
) -> dict[str, str]:
    pulse_strip_dir = output_dir / "pulse_strips"
    pulse_strip_dir.mkdir(parents=True, exist_ok=True)
    slowmo_dir = output_dir / "slowmo_frames"
    slowmo_dir.mkdir(parents=True, exist_ok=True)
    phase_frame_map: dict[int, list[np.ndarray]] = {offset: [] for offset in phase_offsets}
    for pulse in pulses:
        run_frames = frames_by_run[pulse.run_id]
        for offset in phase_offsets:
            frame = run_frames.get(max(0, pulse.matched_frame_index + offset))
            if frame is not None:
                phase_frame_map[offset].append(frame)

    slowmo_images: list[Image.Image] = []
    for offset in phase_offsets:
        phase_frames = phase_frame_map[offset]
        if not phase_frames:
            continue
        averaged_phase = _stack_average(phase_frames)
        label = f"{_phase_label(offset)} ({offset:+d})\nn={len(phase_frames)}"
        labeled = _label_image(averaged_phase, label)
        slowmo_frame_path = slowmo_dir / f"phase_{offset:+d}.png"
        labeled.save(slowmo_frame_path)
        slowmo_images.append(labeled)

    slowmo_path = output_dir / "slowmo_reconstruction.gif"
    if slowmo_images:
        slowmo_images[0].save(
            slowmo_path,
            save_all=True,
            append_images=slowmo_images[1:],
            duration=450,
            loop=0,
        )

    selected_run_ids = set(selected_runs["run_id"].tolist())
    for run_id in selected_run_ids:
        run_pulses = [pulse for pulse in pulses if pulse.run_id == run_id][:PULSE_STRIP_PULSES_PER_RUN]
        if not run_pulses:
            continue
        rows: list[Image.Image] = []
        for pulse in run_pulses:
            tiles: list[Image.Image] = []
            for offset in PULSE_STRIP_OFFSETS:
                frame = frames_by_run[run_id].get(max(0, pulse.matched_frame_index + offset))
                if frame is None:
                    continue
                tiles.append(_label_image(frame, f"pulse {pulse.pulse_index:02d}\n{_phase_label(offset)} {offset:+d}"))
            if tiles:
                rows.append(_concat_horizontal(tiles))
        if rows:
            strip_path = pulse_strip_dir / f"{run_id}_pulse_strip.png"
            _concat_vertical(rows).save(strip_path)

    return {
        "slowmo_reconstruction": _display_path(slowmo_path, repo_root),
        "pulse_strips_dir": _display_path(pulse_strip_dir, repo_root),
        "slowmo_frames_dir": _display_path(slowmo_dir, repo_root),
    }


def _build_comparison_panel(
    repo_root: Path,
    output_dir: Path,
    selected_runs: pd.DataFrame,
    statistics: pd.DataFrame,
    phase_offsets: tuple[int, ...],
) -> str:
    phase_order = list(phase_offsets)
    panel_rows: list[Image.Image] = []
    group_order = list(COMPARISON_GROUP_ORDER) + selected_runs["run_id"].tolist()
    tile_width = tile_height = None
    for group_id in group_order:
        group_stats = statistics.loc[statistics["group_id"] == group_id].copy()
        if group_stats.empty:
            continue
        phase_tiles: list[Image.Image] = []
        for offset in phase_order:
            phase_row = group_stats.loc[group_stats["phase_offset"] == offset]
            if phase_row.empty:
                continue
            row = phase_row.iloc[0]
            with Image.open(repo_root / str(row["preview_path"])) as image:
                tile = _label_image(
                    np.array(image.convert("RGB"), dtype=np.uint8),
                    f"{row['phase_label']} ({offset:+d})\nΔI={row['delta_mean_gray_vs_before']:.1f} px\nn={int(row['frame_count'])}",
                )
            tile_width = tile.width
            tile_height = tile.height
            phase_tiles.append(tile)
        if not phase_tiles or tile_width is None or tile_height is None:
            continue
        first = group_stats.iloc[0]
        run_label = "pooled" if group_id == "pooled" else str(group_id).replace("random-train_", "")
        info_tile = _text_tile(
            tile_width,
            tile_height,
            run_label,
            [
                f"matched={int(first['matched_pulses'])}",
                f"eff_n={float(first['effective_sample_size']):.2f}",
                f"rate={float(first['coincidence_success_rate_windowed']):.2f}",
                f"95% CI [{float(first['coincidence_success_ci_low']):.2f}, {float(first['coincidence_success_ci_high']):.2f}]",
                f"coverage={float(first['coverage_fraction']):.2f}",
                f"mean dt={float(first['mean_offset_ms_detected']):.1f} ms",
            ],
        )
        panel_rows.append(_concat_horizontal([info_tile, *phase_tiles]))

    panel_path = output_dir / "reconstruction_comparison_panel.png"
    if panel_rows:
        _concat_vertical(panel_rows).save(panel_path)
    return _display_path(panel_path, repo_root)


def _build_offset_distribution(
    repo_root: Path,
    output_dir: Path,
    pulses: list[ReconstructionPulse],
) -> str:
    frame = pd.DataFrame(
        {
            "run_id": [pulse.run_id for pulse in pulses],
            "offset_ms": [pulse.matched_frame_dt_ms for pulse in pulses],
        }
    )
    frame["run_short"] = frame["run_id"].str.replace("random-train_", "", regex=False)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
    axes[0].hist(frame["offset_ms"], bins=min(10, max(len(frame), 3)), color="tab:purple", alpha=0.8, edgecolor="white")
    axes[0].axvline(frame["offset_ms"].mean(), color="black", linestyle="--", linewidth=1.2)
    axes[0].set_title("Matched-frame offset distribution")
    axes[0].set_xlabel("Offset OP598 -> webcam matched frame (ms)")
    axes[0].set_ylabel("Pulse count")

    grouped = [frame.loc[frame["run_short"] == run_short, "offset_ms"].tolist() for run_short in frame["run_short"].unique()]
    axes[1].boxplot(grouped, labels=frame["run_short"].unique(), vert=True)
    axes[1].set_title("Run-to-run offset spread")
    axes[1].set_xlabel("Selected run")
    axes[1].set_ylabel("Offset (ms)")
    axes[1].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    offset_path = output_dir / "coincidence_offset_distribution.png"
    fig.savefig(offset_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return _display_path(offset_path, repo_root)


def build_reconstruction_artifacts(
    repo_root: Path,
    selected_runs: pd.DataFrame,
    pulses: list[ReconstructionPulse],
    frames_by_run: dict[str, dict[int, np.ndarray]],
    coincidence_tables: dict[str, pd.DataFrame],
    output_dir: Path,
    phase_offsets: tuple[int, ...] = DEFAULT_PHASE_OFFSETS,
) -> tuple[dict[str, str], pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = _build_avg_and_heatmap(repo_root, output_dir, pulses, frames_by_run)
    artifacts.update(_build_slowmo_and_pulse_strips(repo_root, output_dir, selected_runs, pulses, frames_by_run, phase_offsets))

    statistics, _preview_paths = _build_phase_rows(
        repo_root,
        output_dir,
        selected_runs,
        pulses,
        frames_by_run,
        coincidence_tables,
        phase_offsets,
    )
    statistics_path = output_dir / "reconstruction_statistics.csv"
    statistics.to_csv(statistics_path, index=False)
    artifacts["reconstruction_statistics"] = _display_path(statistics_path, repo_root)

    artifacts["reconstruction_comparison_panel"] = _build_comparison_panel(
        repo_root,
        output_dir,
        selected_runs,
        statistics,
        phase_offsets,
    )
    artifacts["coincidence_offset_distribution"] = _build_offset_distribution(repo_root, output_dir, pulses)
    return artifacts, statistics


def write_selection_csv(repo_root: Path, ranked_runs: pd.DataFrame, output_dir: Path) -> Path:
    path = output_dir / "best_dual_run_selection.csv"
    ranked_runs.to_csv(path, index=False)
    return path


def write_reconstruction_confidence_notes(
    repo_root: Path,
    output_dir: Path,
    selected_runs: pd.DataFrame,
    pulses: list[ReconstructionPulse],
    statistics: pd.DataFrame,
) -> Path:
    pooled = statistics.loc[(statistics["group_id"] == "pooled") & (statistics["phase_offset"] == 0)].iloc[0]
    per_run = statistics.loc[(statistics["group_type"] == "run") & (statistics["phase_offset"] == 0)].copy()
    per_run_excerpt = per_run[
        [
            "run_id",
            "matched_pulses",
            "coverage_fraction",
            "coincidence_success_rate_windowed",
            "coincidence_success_ci_low",
            "coincidence_success_ci_high",
            "mean_offset_ms_detected",
            "offset_std_ms_detected",
        ]
    ].to_markdown(index=False)
    path = output_dir / "reconstruction_confidence_notes.md"
    lines = [
        "# Confidence and coverage notes for the reconstruction",
        "",
        "## How each image was built",
        "",
        "1. Select the best dual random-train runs with full webcam coverage and non-zero matched detections.",
        "2. For each matched pulse, extract webcam frames at relative offsets `-2, -1, 0, +1, +2` around the matched frame.",
        "3. Average pixel-wise within each relative phase to obtain `before`, `approach`, `hit`, `decay`, and `after` views.",
        "4. Create contrast-normalized previews from those averages so the repeated flash pattern is visible without claiming radiometric calibration.",
        "5. Report quantitative deltas against the pooled `before` phase in `reconstruction_statistics.csv`.",
        "",
        "## Coverage and confidence annotations",
        "",
        f"- Selected runs: `{len(selected_runs)}`.",
        f"- Matched pulses contributing to the pooled reconstruction: `{len(pulses)}`.",
        f"- Effective sample size across runs (Kish-style by matched-pulse contribution): `{float(pooled['effective_sample_size']):.2f}`.",
        f"- Pooled coincidence rate on covered windows: `{float(pooled['coincidence_success_rate_windowed']):.3f}` with Wilson 95% CI `[{float(pooled['coincidence_success_ci_low']):.3f}, {float(pooled['coincidence_success_ci_high']):.3f}]`.",
        f"- Pooled mean matched-frame offset: `{float(pooled['mean_offset_ms_detected']):.2f} ms`.",
        "",
        "## Run-level variability at the hit phase",
        "",
        per_run_excerpt,
        "",
        "## Interpretation discipline",
        "",
        "- Higher `frame_count` means more repeated evidence contributed to that phase average.",
        "- `effective_sample_size` tells you whether the pooled image comes from several runs or is dominated by one run.",
        "- `delta_mean_gray_vs_before` is a simple summary of how much brighter a phase is than the pooled pre-flash phase; it is useful for interpretability, not for absolute photometry.",
        "- The comparison panel should be read together with the confidence intervals and offset spread, not as standalone proof of high-speed temporal imaging.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_reconstruction_overview(
    repo_root: Path,
    output_dir: Path,
    ranked_runs: pd.DataFrame,
    selected_runs: pd.DataFrame,
    pulses: list[ReconstructionPulse],
    artifact_paths: dict[str, str],
    statistics: pd.DataFrame,
    uncertainty_artifacts: dict[str, object],
    phase_offsets: tuple[int, ...] = DEFAULT_PHASE_OFFSETS,
) -> Path:
    selected_table = selected_runs[
        [
            "selection_rank",
            "run_id",
            "variant",
            "covered_pulses",
            "matched_detected",
            "coincidence_success_rate_windowed",
            "mean_offset_ms_detected",
        ]
    ].to_markdown(index=False)

    ranked_excerpt = ranked_runs[
        [
            "run_id",
            "variant",
            "coverage_fraction",
            "matched_detected",
            "coincidence_success_rate_windowed",
            "selected_for_reconstruction",
            "selection_reason",
        ]
    ].to_markdown(index=False)
    pooled_hit = statistics.loc[(statistics["group_id"] == "pooled") & (statistics["phase_offset"] == 0)].iloc[0]
    path = output_dir / "reconstruction_overview.md"
    lines = [
        "# Reconstruccion estadistica del evento",
        "",
        "## Que es esta reconstruccion",
        "",
        "- Es una reconstruccion estadistica por coincidencias repetidas entre el ancla temporal OP598 y frames webcam cercanos.",
        "- NO es video de alta velocidad ni imagen directa de un solo destello resuelta frame a frame.",
        "- El panel comparativo agrega fases `before -> approach -> hit -> decay -> after` tanto en pooled como por corrida.",
        "",
        "## Criterio de seleccion de corridas",
        "",
        "1. Priorizar cobertura webcam completa (`limited_coverage=false`).",
        "2. Priorizar mayor tasa de coincidencia en ventanas cubiertas.",
        "3. Desempatar por cantidad de pulsos emparejados y por la variante `phase2_statistical_reconstruction_matrix`.",
        "4. Usar recencia solo como ultimo desempate entre corridas equivalentes.",
        "",
        f"Pulsos acumulados en la reconstruccion: `{len(pulses)}`.",
        f"ESS pooled entre corridas: `{float(pooled_hit['effective_sample_size']):.2f}`.",
        f"Coincidencia pooled: `{float(pooled_hit['coincidence_success_rate_windowed']):.3f}` con IC95% `[{float(pooled_hit['coincidence_success_ci_low']):.3f}, {float(pooled_hit['coincidence_success_ci_high']):.3f}]`.",
        "",
        "## Corridas elegidas",
        "",
        selected_table,
        "",
        "## Ranking completo",
        "",
        ranked_excerpt,
        "",
        "## Artefactos generados",
        "",
        f"- `avg_flash_frame.png`: `{artifact_paths['avg_flash_frame']}`",
        f"- `flash_heatmap.png`: `{artifact_paths['flash_heatmap']}`",
        f"- `reconstruction_comparison_panel.png`: `{artifact_paths['reconstruction_comparison_panel']}`",
        f"- `coincidence_offset_distribution.png`: `{artifact_paths['coincidence_offset_distribution']}`",
        f"- `reconstruction_statistics.csv`: `{artifact_paths['reconstruction_statistics']}`",
        f"- `reconstruction_confidence_notes.md`: `{artifact_paths['reconstruction_confidence_notes']}`",
        f"- `reconstruction_uncertainty_summary.md`: `{artifact_paths['reconstruction_uncertainty_summary']}`",
        f"- `pulse_strips/`: `{artifact_paths['pulse_strips_dir']}`",
        f"- `slowmo_frames/`: `{artifact_paths['slowmo_frames_dir']}`",
        f"- `slowmo_reconstruction.gif`: `{artifact_paths['slowmo_reconstruction']}`",
        "",
        "## Lectura cuantitativa minima",
        "",
        "- `reconstruction_statistics.csv` resume por corrida y por fase: cantidad de frames, ESS, tasa de coincidencia con IC95%, offset medio y diferencia de brillo contra `before`.",
        "- El panel comparativo permite ver si la fase `hit` se mantiene visualmente entre corridas o si una sola corrida domina el pooled.",
        "- El histograma/boxplot de offsets permite ver si el anclaje temporal es consistente o si la reconstruccion junta eventos con offsets muy distintos.",
        "",
        "## Supuestos del metodo",
        "",
        "- El tiempo OP598 se usa como ancla temporal aproximada, no como timing fino sub-milisegundo.",
        "- El frame `0` relativo es el frame webcam ya emparejado por la tabla de coincidencia existente.",
        "- Los previews normalizados mejoran interpretabilidad visual, pero no agregan precision radiometrica.",
        "",
        "## Lo que SI permite afirmar",
        "",
        "- Que existe un patron visual repetible cuando se apilan muchas coincidencias buenas.",
        "- Que ahora hay respaldo cuantitativo minimo para esa narrativa: conteos, ESS, IC95%, offsets y comparacion pooled vs por corrida.",
        "- Que la reconstruccion sirve como proxy visual de evento para presentacion offline.",
        "",
        "## Lo que NO permite afirmar",
        "",
        "- No prueba imagen directa del flash con resolucion temporal fina.",
        "- No separa por completo la contribucion del LED, la optica, el rolling/integration de la webcam y el timing grueso del OP598.",
        "- La propagacion de incertidumbre incluida es por intervalos y sensibilidad practica, no una calibracion metrologica completa.",
        "",
        "## Resumen de incertidumbre",
        "",
        f"- Duty detectable condicionado: `{uncertainty_artifacts['minimum_detectable_duty_statement']}`",
        f"- Umbral practico de duracion detectable: `{uncertainty_artifacts['pulse_duration_threshold_statement']}`",
        f"- Offset medio con incertidumbre temporal: `{uncertainty_artifacts['mean_offset_statement']}`",
        "",
        "## Reproducibilidad",
        "",
        "```bash",
        "python scripts/build_statistical_reconstruction.py",
        "python scripts/build_uncertainty_summary.py",
        "```",
        "",
        f"Todos los outputs se escriben en `{_display_path(output_dir, repo_root)}`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_reconstruction(repo_root: Path | None = None, selection_limit: int = DEFAULT_SELECTION_LIMIT) -> dict[str, object]:
    root = find_repo_root(repo_root)
    output_dir = reconstruction_dir(root)
    dual_runs = load_dual_runs(root)
    ranked_runs = rank_dual_runs(dual_runs, selection_limit=selection_limit)
    selected_runs, pulses, coincidence_tables = load_selected_pulses(root, ranked_runs)
    frames_by_run = extract_run_frames(root, selected_runs, pulses)
    selection_csv = write_selection_csv(root, ranked_runs, output_dir)
    artifacts, statistics = build_reconstruction_artifacts(root, selected_runs, pulses, frames_by_run, coincidence_tables, output_dir)
    confidence_notes = write_reconstruction_confidence_notes(root, output_dir, selected_runs, pulses, statistics)
    artifacts["reconstruction_confidence_notes"] = _display_path(confidence_notes, root)
    uncertainty_artifacts = build_uncertainty_summary(root, selected_runs, coincidence_tables, output_dir)
    artifacts["reconstruction_uncertainty_summary"] = str(uncertainty_artifacts["summary_path"])
    overview = write_reconstruction_overview(
        root,
        output_dir,
        ranked_runs,
        selected_runs,
        pulses,
        artifacts,
        statistics,
        uncertainty_artifacts,
    )
    return {
        "repo_root": str(root),
        "output_dir": str(output_dir),
        "selection_csv": str(selection_csv),
        "overview_md": str(overview),
        "selected_runs": selected_runs["run_id"].tolist(),
        "pulse_count": len(pulses),
        "artifacts": artifacts,
        "uncertainty": {
            key: value
            for key, value in uncertainty_artifacts.items()
            if key != "summary_path"
        },
    }
