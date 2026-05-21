"""
Probe USB webcam capture settings and record short clips with OpenCV.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import platform
import struct
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import cv2
except ImportError as exc:  # pragma: no cover - exercised only without dependency
    raise SystemExit(
        "OpenCV is not installed. Run: python -m pip install -r requirements.txt"
    ) from exc


DEFAULT_BACKEND = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_ANY
PROP_NAMES = (
    ("width", cv2.CAP_PROP_FRAME_WIDTH),
    ("height", cv2.CAP_PROP_FRAME_HEIGHT),
    ("fps", cv2.CAP_PROP_FPS),
    ("fourcc", cv2.CAP_PROP_FOURCC),
    ("convert_rgb", cv2.CAP_PROP_CONVERT_RGB),
    ("buffersize", cv2.CAP_PROP_BUFFERSIZE),
    ("auto_exposure", cv2.CAP_PROP_AUTO_EXPOSURE),
    ("exposure", cv2.CAP_PROP_EXPOSURE),
    ("gain", cv2.CAP_PROP_GAIN),
    ("brightness", cv2.CAP_PROP_BRIGHTNESS),
    ("contrast", cv2.CAP_PROP_CONTRAST),
)

AUTO_EXPOSURE_VALUES = {
    "manual": 0.25,
    "auto": 0.75,
}
V4L2_EXPOSURE_VALUES = {
    "manual": 1,
    "auto": 3,
}
V4L2_CID_EXPOSURE_AUTO = 0x009A0901
V4L2_CID_EXPOSURE_ABSOLUTE = 0x009A0902
V4L2_CID_EXPOSURE_AUTO_PRIORITY = 0x009A0903
V4L2_CONTROL_NAMES = {
    "v4l2_exposure_auto": V4L2_CID_EXPOSURE_AUTO,
    "v4l2_exposure_absolute": V4L2_CID_EXPOSURE_ABSOLUTE,
    "v4l2_exposure_auto_priority": V4L2_CID_EXPOSURE_AUTO_PRIORITY,
}
VIDIOC_G_CTRL = 0xC008561B
VIDIOC_S_CTRL = 0xC008561C


def parse_csv_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_csv_strings(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def fourcc_to_string(value: float) -> str:
    code = int(value)
    chars = [chr((code >> 8 * index) & 0xFF) for index in range(4)]
    text = "".join(chars)
    return text if text.strip("\x00") else "----"


def open_capture(index: int, backend: int) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(index, backend)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Could not open camera index {index}")
    return capture


def device_path(index: int) -> str:
    return f"/dev/video{index}"


def get_v4l2_control(index: int, control_id: int) -> int | None:
    if platform.system() != "Linux":
        return None

    try:
        fd = os.open(device_path(index), os.O_RDWR | os.O_NONBLOCK)
    except OSError:
        return None

    try:
        packed = struct.pack("Ii", control_id, 0)
        unpacked = fcntl.ioctl(fd, VIDIOC_G_CTRL, packed)
        return struct.unpack("Ii", unpacked)[1]
    except OSError:
        return None
    finally:
        os.close(fd)


def set_v4l2_control(index: int, control_id: int, value: int) -> bool:
    if platform.system() != "Linux":
        return False

    try:
        fd = os.open(device_path(index), os.O_RDWR | os.O_NONBLOCK)
    except OSError:
        return False

    try:
        fcntl.ioctl(fd, VIDIOC_S_CTRL, struct.pack("Ii", control_id, value))
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def apply_v4l2_controls(index: int, args: argparse.Namespace) -> None:
    if args.auto_exposure:
        set_v4l2_control(
            index, V4L2_CID_EXPOSURE_AUTO, V4L2_EXPOSURE_VALUES[args.auto_exposure]
        )
        if args.auto_exposure == "manual" and args.exposure_auto_priority is None:
            set_v4l2_control(index, V4L2_CID_EXPOSURE_AUTO_PRIORITY, 0)
    if args.exposure_auto_priority is not None:
        set_v4l2_control(
            index, V4L2_CID_EXPOSURE_AUTO_PRIORITY, args.exposure_auto_priority
        )
    if args.exposure is not None:
        set_v4l2_control(index, V4L2_CID_EXPOSURE_ABSOLUTE, int(args.exposure))


def read_v4l2_controls(index: int) -> dict[str, str]:
    controls: dict[str, str] = {}
    for name, control_id in V4L2_CONTROL_NAMES.items():
        value = get_v4l2_control(index, control_id)
        controls[name] = "n/a" if value is None else str(value)
    return controls


def apply_settings(
    capture: cv2.VideoCapture,
    width: int | None,
    height: int | None,
    fps: int | None,
    fourcc: str | None,
    raw: bool,
    buffer_size: int | None,
) -> None:
    if fourcc:
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc[:4]))
    if width:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height:
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if fps:
        capture.set(cv2.CAP_PROP_FPS, fps)
    if raw:
        capture.set(cv2.CAP_PROP_CONVERT_RGB, 0)
    if buffer_size is not None:
        capture.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)


def frame_for_display(frame, fourcc: str, raw: bool):
    if not raw:
        return frame
    if fourcc.upper().startswith("YUY") and len(frame.shape) == 3 and frame.shape[2] == 2:
        return cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUY2)
    return frame


def apply_camera_controls(capture: cv2.VideoCapture, args: argparse.Namespace) -> None:
    if args.auto_exposure:
        capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, AUTO_EXPOSURE_VALUES[args.auto_exposure])
    if args.exposure is not None:
        capture.set(cv2.CAP_PROP_EXPOSURE, args.exposure)
    if args.gain is not None:
        capture.set(cv2.CAP_PROP_GAIN, args.gain)
    if args.brightness is not None:
        capture.set(cv2.CAP_PROP_BRIGHTNESS, args.brightness)
    if args.contrast is not None:
        capture.set(cv2.CAP_PROP_CONTRAST, args.contrast)


def read_properties(capture: cv2.VideoCapture) -> dict[str, str]:
    props: dict[str, str] = {}
    for name, prop_id in PROP_NAMES:
        value = capture.get(prop_id)
        if name == "fourcc":
            props[name] = fourcc_to_string(value)
        elif name in {"width", "height"}:
            props[name] = str(int(round(value)))
        else:
            props[name] = f"{value:.2f}"
    return props


def measure_fps(
    capture: cv2.VideoCapture,
    seconds: float,
    warmup_seconds: float,
    preview: bool,
    raw: bool,
    fourcc: str,
    window_name: str = "webcam fps probe",
) -> tuple[float, int]:
    warmup_until = time.perf_counter() + warmup_seconds
    while time.perf_counter() < warmup_until:
        capture.read()

    frames = 0
    started = time.perf_counter()
    deadline = started + seconds

    while time.perf_counter() < deadline:
        ok, frame = capture.read()
        if not ok:
            continue

        frames += 1
        if preview:
            cv2.imshow(window_name, frame_for_display(frame, fourcc, raw))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    elapsed = time.perf_counter() - started
    if preview:
        cv2.destroyWindow(window_name)
    return (frames / elapsed if elapsed else 0.0, frames)


def list_cameras(max_index: int, backend: int) -> list[int]:
    found: list[int] = []
    for index in range(max_index + 1):
        capture = cv2.VideoCapture(index, backend)
        if capture.isOpened():
            found.append(index)
        capture.release()
    return found


def print_camera_list(indices: list[int]) -> None:
    if not indices:
        print("No cameras opened through OpenCV.")
        return
    print("OpenCV camera indices:", ", ".join(str(index) for index in indices))


def probe(args: argparse.Namespace) -> int:
    backend = DEFAULT_BACKEND if args.prefer_v4l2 else cv2.CAP_ANY

    cameras: list[int] = []
    if args.list or args.index is None:
        cameras = list_cameras(args.max_index, backend)
        print_camera_list(cameras)

    if args.list:
        return 0

    index = args.index if args.index is not None else (cameras[0] if cameras else 0)
    widths = parse_csv_ints(args.width)
    heights = parse_csv_ints(args.height)
    fps_values = parse_csv_ints(args.fps)
    fourcc_values = parse_csv_strings(args.fourcc)

    print(
        "\nindex req_width req_height req_fps req_fourcc "
        "actual_width actual_height actual_fps actual_fourcc convert_rgb "
        "opencv_auto_exposure v4l2_exposure_auto/absolute opencv_exposure gain "
        "measured_fps frames"
    )
    for fourcc in fourcc_values:
        for width in widths:
            for height in heights:
                for fps in fps_values:
                    try:
                        apply_v4l2_controls(index, args)
                        capture = open_capture(index, backend)
                    except RuntimeError as exc:
                        print(exc)
                        return 1

                    try:
                        apply_settings(
                            capture, width, height, fps, fourcc, args.raw, args.buffer_size
                        )
                        apply_camera_controls(capture, args)
                        props = read_properties(capture)
                        controls = read_v4l2_controls(index)
                        measured_fps, frames = measure_fps(
                            capture,
                            args.seconds,
                            args.warmup,
                            args.preview,
                            args.raw,
                            fourcc,
                        )
                        print(
                            f"{index} {width} {height} {fps} {fourcc} "
                            f"{props['width']} {props['height']} {props['fps']} "
                            f"{props['fourcc']} {props['convert_rgb']} "
                            f"{props['auto_exposure']} "
                            f"{controls['v4l2_exposure_auto']}/"
                            f"{controls['v4l2_exposure_absolute']} "
                            f"{props['exposure']} {props['gain']} "
                            f"{measured_fps:.2f} {frames}"
                        )
                    finally:
                        capture.release()

    return 0


def default_output_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"webcam_clip_{timestamp}.avi"


def record(args: argparse.Namespace) -> int:
    backend = DEFAULT_BACKEND if args.prefer_v4l2 else cv2.CAP_ANY
    output_path = (
        Path(args.output) if args.output else default_output_path(Path(args.output_dir))
    )

    try:
        apply_v4l2_controls(args.index, args)
        capture = open_capture(args.index, backend)
    except RuntimeError as exc:
        print(exc)
        return 1

    writer: cv2.VideoWriter | None = None
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
        actual_width = int(props["width"])
        actual_height = int(props["height"])
        writer_fps = args.write_fps or args.fps or float(props["fps"]) or 30.0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*args.output_fourcc[:4]),
            float(writer_fps),
            (actual_width, actual_height),
        )
        if not writer.isOpened():
            print(f"Could not open video writer for {output_path}")
            return 1

        frames = 0
        warmup_until = time.perf_counter() + args.warmup
        while time.perf_counter() < warmup_until:
            capture.read()

        started = time.perf_counter()
        deadline = started + args.seconds
        while time.perf_counter() < deadline:
            ok, frame = capture.read()
            if not ok:
                continue

            writer.write(frame_for_display(frame, args.fourcc, args.raw))
            frames += 1
            if args.preview:
                cv2.imshow(
                    "webcam record", frame_for_display(frame, args.fourcc, args.raw)
                )
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        elapsed = time.perf_counter() - started
        measured_fps = frames / elapsed if elapsed else 0.0
        print(f"Output: {output_path}")
        print(
            "Actual capture: "
            f"{props['width']}x{props['height']} "
            f"{props['fps']} fps {props['fourcc']} "
            f"convert_rgb={props['convert_rgb']} "
            f"auto_exposure={props['auto_exposure']} "
            f"v4l2_exposure={controls['v4l2_exposure_auto']}/"
            f"{controls['v4l2_exposure_absolute']} "
            f"exposure={props['exposure']} gain={props['gain']}"
        )
        print(f"Frames written: {frames}")
        print(f"Measured delivered FPS: {measured_fps:.2f}")
        print(f"Video writer FPS metadata: {float(writer_fps):.2f}")
        return 0
    finally:
        if writer is not None:
            writer.release()
        capture.release()
        if args.preview:
            cv2.destroyAllWindows()


def add_camera_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--index", type=int, help="OpenCV camera index")
    parser.add_argument("--width", default="640", help="Width or comma list of widths")
    parser.add_argument(
        "--height", default="480", help="Height or comma list of heights"
    )
    parser.add_argument("--fps", default="30", help="FPS or comma list of FPS values")
    parser.add_argument("--fourcc", default="MJPG", help="Capture FOURCC or comma list")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Disable OpenCV RGB conversion. Useful for measuring true camera throughput",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        help="Requested OpenCV capture buffer size. Leave unset for backend default; 1 can lower latency but may reduce FPS",
    )
    parser.add_argument(
        "--no-v4l2",
        action="store_false",
        dest="prefer_v4l2",
        help="Use OpenCV's default backend instead of CAP_V4L2 on Linux",
    )
    parser.set_defaults(prefer_v4l2=True)


def add_control_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--auto-exposure",
        choices=sorted(AUTO_EXPOSURE_VALUES),
        help="Request auto or manual exposure mode; manual often improves FPS stability",
    )
    parser.add_argument(
        "--exposure",
        type=float,
        help="Requested exposure value. V4L2/OpenCV units are camera-dependent",
    )
    parser.add_argument("--gain", type=float, help="Requested camera gain")
    parser.add_argument(
        "--exposure-auto-priority",
        type=int,
        choices=(0, 1),
        help="Linux UVC control: 0 keeps FPS stable, 1 allows exposure to lower FPS",
    )
    parser.add_argument("--brightness", type=float, help="Requested camera brightness")
    parser.add_argument("--contrast", type=float, help="Requested camera contrast")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe and record USB webcam FPS with OpenCV."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe_parser = subparsers.add_parser(
        "probe", help="List cameras and measure delivered FPS"
    )
    add_camera_options(probe_parser)
    add_control_options(probe_parser)
    probe_parser.add_argument(
        "--seconds", type=float, default=3.0, help="Sampling window"
    )
    probe_parser.add_argument(
        "--warmup", type=float, default=1.0, help="Warmup seconds before measuring"
    )
    probe_parser.add_argument(
        "--max-index", type=int, default=8, help="Highest camera index to try"
    )
    probe_parser.add_argument(
        "--list", action="store_true", help="Only list camera indices"
    )
    probe_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show frames while probing; press q to stop",
    )
    probe_parser.set_defaults(func=probe)

    record_parser = subparsers.add_parser(
        "record", help="Record a short clip and report delivered FPS"
    )
    record_parser.add_argument(
        "--index", type=int, default=0, help="OpenCV camera index"
    )
    record_parser.add_argument("--width", type=int, default=640, help="Requested width")
    record_parser.add_argument(
        "--height", type=int, default=480, help="Requested height"
    )
    record_parser.add_argument(
        "--fps", type=int, default=30, help="Requested capture FPS"
    )
    record_parser.add_argument(
        "--fourcc", default="MJPG", help="Requested capture FOURCC"
    )
    add_control_options(record_parser)
    record_parser.add_argument(
        "--seconds", type=float, default=5.0, help="Clip duration"
    )
    record_parser.add_argument(
        "--warmup", type=float, default=1.0, help="Warmup seconds before recording"
    )
    record_parser.add_argument("--output", help="Output video path")
    record_parser.add_argument(
        "--output-dir", default="data/webcam", help="Default clip directory"
    )
    record_parser.add_argument(
        "--output-fourcc", default="MJPG", help="Video writer FOURCC"
    )
    record_parser.add_argument(
        "--write-fps", type=float, help="Video file FPS metadata"
    )
    record_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show frames while recording; press q to stop",
    )
    record_parser.add_argument(
        "--no-v4l2",
        action="store_false",
        dest="prefer_v4l2",
        help="Use OpenCV's default backend instead of CAP_V4L2 on Linux",
    )
    record_parser.set_defaults(func=record, prefer_v4l2=True)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
