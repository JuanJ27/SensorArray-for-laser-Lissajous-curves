"""
Detect LED flashes in a dark box using a USB webcam and OpenCV.
"""

from __future__ import annotations

import argparse
import csv
import platform
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    import cv2
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit(
        "OpenCV is not installed. Run: python -m pip install -r requirements.txt"
    ) from exc

from webcam_fps_tool import (  # noqa: E402
    apply_camera_controls,
    apply_settings,
    apply_v4l2_controls,
    frame_for_display,
    open_capture,
    read_properties,
    read_v4l2_controls,
)


DEFAULT_BACKEND = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_ANY
CSV_FIELDS = (
    "timestamp_s",
    "perf_counter_s",
    "frame_index",
    "mean",
    "max",
    "p99",
    "threshold",
    "detected",
)


def parse_roi(value: str) -> tuple[int, int, int, int]:
    parts = [int(item.strip()) for item in value.split(",") if item.strip()]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("ROI must be x,y,w,h")
    x, y, width, height = parts
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("ROI width and height must be positive")
    return x, y, width, height


def default_csv_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"webcam_flash_metrics_{timestamp}.csv"


def luma_frame(frame: np.ndarray, fourcc: str, raw: bool) -> np.ndarray:
    if raw and fourcc.upper().startswith("YUY") and frame.ndim == 3 and frame.shape[2] == 2:
        return frame[:, :, 0]
    if frame.ndim == 2:
        return frame
    if frame.ndim == 3 and frame.shape[2] == 1:
        return frame[:, :, 0]
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def crop_roi(gray: np.ndarray, roi: tuple[int, int, int, int] | None) -> np.ndarray:
    if roi is None:
        return gray
    x, y, width, height = roi
    frame_height, frame_width = gray.shape[:2]
    x0 = max(0, min(x, frame_width - 1))
    y0 = max(0, min(y, frame_height - 1))
    x1 = max(x0 + 1, min(x0 + width, frame_width))
    y1 = max(y0 + 1, min(y0 + height, frame_height))
    return gray[y0:y1, x0:x1]


def compute_metrics(gray: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean(gray)),
        "max": float(np.max(gray)),
        "p99": float(np.percentile(gray, 99)),
    }


def metric_value(metrics: dict[str, float], name: str) -> float:
    return metrics[name]


def select_interactive_roi(
    capture: cv2.VideoCapture, fourcc: str, raw: bool
) -> tuple[int, int, int, int] | None:
    ok, frame = capture.read()
    if not ok:
        print("Could not read a frame for interactive ROI; using full frame.")
        return None

    display = frame_for_display(frame, fourcc, raw)
    selected = cv2.selectROI("select flash ROI", display, showCrosshair=True)
    cv2.destroyWindow("select flash ROI")
    x, y, width, height = [int(value) for value in selected]
    if width <= 0 or height <= 0:
        print("Empty ROI selected; using full frame.")
        return None
    return x, y, width, height


def draw_overlay(
    frame: np.ndarray,
    roi: tuple[int, int, int, int] | None,
    detected: bool,
    metric_name: str,
    metric: float,
    threshold: float,
) -> np.ndarray:
    output = frame.copy()
    if roi is not None:
        x, y, width, height = roi
        color = (0, 0, 255) if detected else (0, 255, 0)
        cv2.rectangle(output, (x, y), (x + width, y + height), color, 2)
    status = "FLASH" if detected else "dark"
    cv2.putText(
        output,
        f"{status} {metric_name}={metric:.1f} thr={threshold:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255) if detected else (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    return output


def collect_baseline(
    capture: cv2.VideoCapture,
    args: argparse.Namespace,
    roi: tuple[int, int, int, int] | None,
) -> tuple[float, float, int]:
    values: list[float] = []
    deadline = time.perf_counter() + args.calibration
    while time.perf_counter() < deadline:
        ok, frame = capture.read()
        if not ok:
            continue
        gray = crop_roi(luma_frame(frame, args.fourcc, args.raw), roi)
        metrics = compute_metrics(gray)
        values.append(metric_value(metrics, args.metric))
        if args.preview:
            cv2.imshow("webcam flash detector", frame_for_display(frame, args.fourcc, args.raw))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if not values:
        raise RuntimeError("No frames captured during baseline calibration")

    return float(np.mean(values)), float(np.std(values)), len(values)


def threshold_from_baseline(baseline: float, sigma: float, args: argparse.Namespace) -> float:
    candidates = []
    if args.threshold_delta is not None:
        candidates.append(baseline + args.threshold_delta)
    if args.sigma_multiplier is not None:
        candidates.append(baseline + args.sigma_multiplier * sigma)
    return max(candidates) if candidates else baseline + 20.0


def run_detection(args: argparse.Namespace) -> int:
    backend = DEFAULT_BACKEND if args.prefer_v4l2 else cv2.CAP_ANY
    output_path = Path(args.output) if args.output else default_csv_path(Path(args.output_dir))
    frames_dir = Path(args.frames_dir) if args.frames_dir else output_path.with_suffix("")
    video_path = Path(args.video_output) if args.video_output else None

    try:
        apply_v4l2_controls(args.index, args)
        capture = open_capture(args.index, backend)
    except RuntimeError as exc:
        print(exc)
        return 1

    try:
        apply_settings(
            capture,
            args.width,
            args.height,
            args.fps,
            args.fourcc,
            args.raw,
            args.buffer_size,
        )
        apply_camera_controls(capture, args)
        props = read_properties(capture)
        controls = read_v4l2_controls(args.index)

        roi = args.roi
        if args.select_roi:
            roi = select_interactive_roi(capture, args.fourcc, args.raw)

        warmup_until = time.perf_counter() + args.warmup
        while time.perf_counter() < warmup_until:
            capture.read()

        baseline, sigma, baseline_frames = collect_baseline(capture, args, roi)
        threshold = threshold_from_baseline(baseline, sigma, args)
        print(
            "Baseline: "
            f"metric={args.metric} mean={baseline:.2f} sigma={sigma:.2f} "
            f"threshold={threshold:.2f} frames={baseline_frames}"
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.save_detected_frames:
            frames_dir.mkdir(parents=True, exist_ok=True)
        if video_path is not None:
            video_path.parent.mkdir(parents=True, exist_ok=True)

        detections = 0
        detection_events = 0
        frames = 0
        in_flash = False
        rows: deque[dict[str, float | int | bool]] = deque()
        started = time.perf_counter()
        deadline = started + args.seconds
        last_status = started
        writer_video: cv2.VideoWriter | None = None

        print(
            "Actual capture: "
            f"{props['width']}x{props['height']} {props['fps']} fps "
            f"{props['fourcc']} convert_rgb={props['convert_rgb']} "
            f"auto_exposure={props['auto_exposure']} "
            f"v4l2_exposure={controls['v4l2_exposure_auto']}/"
            f"{controls['v4l2_exposure_absolute']} exposure={props['exposure']}"
        )

        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()

            while time.perf_counter() < deadline:
                ok, frame = capture.read()
                if not ok:
                    continue

                now = time.perf_counter()
                display_frame = frame_for_display(frame, args.fourcc, args.raw)
                if writer_video is None and video_path is not None:
                    height, width = display_frame.shape[:2]
                    writer_video = cv2.VideoWriter(
                        str(video_path),
                        cv2.VideoWriter_fourcc(*"MJPG"),
                        float(props["fps"] or args.fps or 30),
                        (width, height),
                    )
                    if not writer_video.isOpened():
                        raise RuntimeError(f"Could not open webcam video output: {video_path}")
                if writer_video is not None:
                    writer_video.write(display_frame)

                gray = crop_roi(luma_frame(frame, args.fourcc, args.raw), roi)
                metrics = compute_metrics(gray)
                current_metric = metric_value(metrics, args.metric)
                detected = current_metric >= threshold

                if detected:
                    detections += 1
                    if not in_flash:
                        detection_events += 1
                    in_flash = True
                elif current_metric < threshold - args.hysteresis:
                    in_flash = False

                frame_index = frames
                row = {
                    "timestamp_s": now - started,
                    "perf_counter_s": now,
                    "frame_index": frame_index,
                    "mean": metrics["mean"],
                    "max": metrics["max"],
                    "p99": metrics["p99"],
                    "threshold": threshold,
                    "detected": int(detected),
                }
                writer.writerow(row)
                rows.append(row)
                if len(rows) > 5:
                    rows.popleft()

                if detected and args.save_detected_frames:
                    cv2.imwrite(str(frames_dir / f"flash_{frame_index:06d}.png"), display_frame)

                if args.preview:
                    overlay = draw_overlay(
                        display_frame,
                        roi,
                        detected,
                        args.metric,
                        current_metric,
                        threshold,
                    )
                    cv2.imshow("webcam flash detector", overlay)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                frames += 1
                if now - last_status >= args.status_interval:
                    csv_file.flush()
                    elapsed = now - started
                    fps = frames / elapsed if elapsed else 0.0
                    print(
                        f"t={elapsed:.1f}s frames={frames} fps={fps:.2f} "
                        f"{args.metric}={current_metric:.1f} detections={detections} "
                        f"events={detection_events}"
                    )
                    last_status = now

            csv_file.flush()

        elapsed = time.perf_counter() - started
        measured_fps = frames / elapsed if elapsed else 0.0
        print("Summary:")
        print(f"  Frames: {frames}")
        print(f"  Measured FPS: {measured_fps:.2f}")
        print(f"  Detected frames: {detections}")
        print(f"  Detection events: {detection_events}")
        print(f"  CSV: {output_path}")
        if args.save_detected_frames:
            print(f"  Detected frames directory: {frames_dir}")
        if video_path is not None:
            print(f"  Video: {video_path}")
        return 0
    finally:
        if 'writer_video' in locals() and writer_video is not None:
            writer_video.release()
        capture.release()
        if args.preview or args.select_roi:
            cv2.destroyAllWindows()


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--index", type=int, default=2, help="OpenCV camera index")
    parser.add_argument("--width", type=int, default=640, help="Requested width")
    parser.add_argument("--height", type=int, default=480, help="Requested height")
    parser.add_argument("--fps", type=int, default=30, help="Requested capture FPS")
    parser.add_argument("--fourcc", default="YUYV", help="Requested capture FOURCC")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Disable OpenCV RGB conversion; useful with YUYV on the C525",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        help="Requested capture buffer size; leave unset for the C525 30 FPS path",
    )
    parser.add_argument(
        "--no-v4l2",
        action="store_false",
        dest="prefer_v4l2",
        help="Use OpenCV's default backend instead of CAP_V4L2 on Linux",
    )
    parser.set_defaults(prefer_v4l2=True)
    parser.add_argument("--auto-exposure", choices=("auto", "manual"))
    parser.add_argument("--exposure", type=float, help="Camera exposure value")
    parser.add_argument("--gain", type=float, help="Camera gain")
    parser.add_argument("--brightness", type=float, help="Camera brightness")
    parser.add_argument("--contrast", type=float, help="Camera contrast")
    parser.add_argument(
        "--exposure-auto-priority",
        type=int,
        choices=(0, 1),
        help="Linux UVC control: 0 keeps FPS stable, 1 allows exposure to lower FPS",
    )
    parser.add_argument("--seconds", type=float, default=10.0, help="Detection window")
    parser.add_argument("--warmup", type=float, default=1.0, help="Warmup before baseline")
    parser.add_argument(
        "--calibration", type=float, default=3.0, help="Dark baseline seconds"
    )
    parser.add_argument(
        "--metric",
        choices=("mean", "max", "p99"),
        default="p99",
        help="Metric used for threshold detection",
    )
    parser.add_argument(
        "--threshold-delta",
        type=float,
        default=20.0,
        help="Absolute threshold above baseline metric",
    )
    parser.add_argument(
        "--sigma-multiplier",
        type=float,
        default=5.0,
        help="Threshold also considers baseline + multiplier * sigma",
    )
    parser.add_argument(
        "--hysteresis",
        type=float,
        default=5.0,
        help="Metric drop below threshold before a new event is counted",
    )
    parser.add_argument("--roi", type=parse_roi, help="Manual ROI as x,y,w,h")
    parser.add_argument(
        "--select-roi",
        action="store_true",
        help="Select ROI interactively from the first frame",
    )
    parser.add_argument(
        "--preview", action="store_true", help="Show live preview; press q to stop"
    )
    parser.add_argument("--output", help="CSV output path")
    parser.add_argument(
        "--output-dir", default="data/webcam", help="Default CSV output directory"
    )
    parser.add_argument(
        "--save-detected-frames",
        action="store_true",
        help="Save PNG frames where the detector crosses threshold",
    )
    parser.add_argument("--frames-dir", help="Directory for detected PNG frames")
    parser.add_argument("--video-output", help="Optional MJPG AVI path for the full webcam run")
    parser.add_argument(
        "--status-interval", type=float, default=1.0, help="Live status period in seconds"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect LED flashes in a dark box using webcam intensity metrics."
    )
    add_arguments(parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_detection(args)


if __name__ == "__main__":
    sys.exit(main())
