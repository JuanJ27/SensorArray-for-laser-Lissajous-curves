# Webcam LED flash experiment results - 2026-05-21

These are sonoluminescence-analogue detectability tests only. This setup does not create actual sonoluminescence; it uses a controlled external LED on ESP32 `GPIO17` to emulate short, weak flashes in a dark box.

## Hardware state

| Item | Result |
|------|--------|
| Red ESP32 power LED | Must be physically taped/covered; treated as not software-controllable. |
| Blue onboard LED | Controlled only on known candidate `GPIO2`; `boardled off` writes value `0`. |
| External experimental LED | Controlled by PWM on `GPIO17`. |

## Firmware/serial verification

```text
> boardled off
OK boardled pin=2 state=off value=0

> status
OK status duty=0 freq=1000 onboard_led_pin=2 onboard_led_value=0 pin=17

> off
OK off duty=0
```

Final post-test state:

```text
OK status duty=0 freq=1000 onboard_led_pin=2 onboard_led_value=0 pin=17
```

## Full integrated flash test

Command shape:

```bash
python tools/run_led_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --count 5 --period-ms 1000 --duration-ms 300 --duty 1023 \
  --seconds 12 --warmup 1 --calibration 3 --preview
```

| Metric | Value |
|--------|-------|
| Frames | 359 |
| Measured FPS | 29.88 |
| Detected frames | 46 |
| Detection events | 5 |
| Expected pulses | 5 |
| CSV | `data/webcam/webcam_flash_metrics_20260521_114151.csv` |

Preview produced Qt/font warnings, but the detector continued and saved data.

## Intensity threshold sweep

Command shape:

```bash
python tools/run_led_intensity_sweep.py \
  --port /dev/ttyUSB0 \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --duties 8,16,24,32,48,64,96,128,192,256,384,512,768,1023 \
  --count 3 --period-ms 700 --duration-ms 200
```

| Result | Value |
|--------|-------|
| Summary CSV | `data/webcam/led_intensity_sweep_20260521_114216.csv` |
| Minimum detected duty | `8` |
| Detection result | Every tested duty produced 3 detection events. |

## Exposure and pulse-duration sweep

Command shape:

```bash
python tools/run_flash_parameter_sweep.py \
  --port /dev/ttyUSB0 \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --metric max --threshold-delta 30 \
  --duty 8 --count 3 --period-ms 700 --duration-ms 50 \
  --exposure 10 --exposures 1,3,5,10,20,40 \
  --durations-ms 5,10,20,50,100,200,300
```

| Sweep | Notable result |
|-------|----------------|
| Exposure at `duty=8`, `duration=50 ms` | Exposure `3` detected 0 events in this run; exposure `5`, `10`, `20`, and `40` detected all 3 events. Exposure `1` was clamped by the camera to `3` and detected 2 events. |
| Duration at `duty=8`, `exposure=10` | `5`, `10`, and `20 ms` detected 0 events; `50 ms` detected 2 events; `100`, `200`, and `300 ms` detected all 3 events. |
| Summary CSV | `data/webcam/flash_parameter_sweep_20260521_114453.csv` |

## Recommended demo

Use this for a reliable live demo after taping/covering the red power LED:

```bash
./scripts/esp32_all_off.sh
./scripts/flash_experiment.sh
```

If preview fails due Qt/display issues, run the same command without `--preview`; CSV generation does not require preview.
