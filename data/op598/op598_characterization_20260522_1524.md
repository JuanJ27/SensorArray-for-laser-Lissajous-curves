# OP598 characterization 2026-05-22 15:24

## Setup

- OP598 powered from 3.3V.
- Load resistor: 100kOhm to GND.
- ESP32 ADC pin: ADC36 (`verde`).
- External LED: GPIO17.

## Commands run

```bash
.venv/bin/python tools/led_serial_control.py --port /dev/ttyUSB0 --soft-reboot status
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 status
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 50 sample --sample-count 200 --sample-delay 5 --sample-unit ms
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 400 --duty 1023 --pre-ms 80 --post-ms 150 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 100 --duty 1023 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 30 --duty 1023 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 200 --duty 1023 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 200 --duty 512 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 200 --duty 128 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 200 --duty 32 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 pulse --duration-ms 200 --duty 8 --pre-ms 80 --post-ms 120 --sample-us 1000
.venv/bin/python tools/capture_op598_response.py --port /dev/ttyUSB0 --print-every 100 train --count 6 --period-ms 120 --duration-ms 30 --duty 1023 --pre-ms 80 --post-ms 150 --sample-us 1000
```

## Findings

- ADC36 now responds. `sensor status` returned `last_adc=3221`.
- Baseline ambient stream was not pinned at 0 or 4095. Baseline mean was `2973.55` ADC with observed range `2899-3141`.
- Full-scale optical pulses are easy to detect.
- `400 ms @ duty 1023`: baseline `2987.6`, pulse mean `4095.0`, peak `4095`, width `400.6 ms`.
- `100 ms @ duty 1023`: baseline `2989.2`, pulse mean `4023.4`, peak `4095`, width `100.1 ms`.
- `30 ms @ duty 1023`: baseline `2968.6`, pulse mean `4095.0`, peak `4095`, width `27.5 ms`.
- Intensity sweep at `200 ms` shows strong saturation for `1023`, `512`, and `128` since all hit `4095`.
- Lower duties remain below full scale and are more useful for comparative characterization:
- `duty 32`: baseline `2979.1`, pulse mean `3489.9`, peak `3915`.
- `duty 8`: baseline `2980.8`, pulse mean `3197.3`, peak `3307`.
- Repeated pulse train (`6 x 30 ms @ 120 ms period, duty 1023`) produced `pulse_count=6`; every pulse reached `4095`, so pulses are individually detectable but the high-duty regime saturates and leaves recovery tail in the gaps.
- Effective sample interval stayed around `6.4-6.6 ms` despite requesting `1000 us`, so sub-millisecond timing is not available from this ESP32 capture path.

## Assessment

- The OP598 channel is now usable for system-speed flash detection and coarse timing at this mounted setup.
- It is not useful as a linear intensity measurement channel at medium/high LED duty because the ADC saturates quickly.
- For characterization runs on this exact hardware, the most informative unsaturated region is the low-duty range, around `8-32`.

## Artifacts

- Baseline: `data/op598/op598_sample_20260522_152335.csv`
- Baseline summary: `data/op598/op598_sample_20260522_152335_summary.md`
- Long pulse: `data/op598/op598_pulse_profile_20260522_152355.csv`
- Medium pulse: `data/op598/op598_pulse_profile_20260522_152358.csv`
- Short pulse: `data/op598/op598_pulse_profile_20260522_152400.csv`
- Intensity sweep files: `data/op598/op598_pulse_profile_20260522_152402.csv`, `data/op598/op598_pulse_profile_20260522_152404.csv`, `data/op598/op598_pulse_profile_20260522_152407.csv`, `data/op598/op598_pulse_profile_20260522_152409.csv`, `data/op598/op598_pulse_profile_20260522_152412.csv`
- Train file: `data/op598/op598_train_profile_20260522_152414.csv`
- Matching plots and per-run summaries are in the same directory with the same timestamps.
