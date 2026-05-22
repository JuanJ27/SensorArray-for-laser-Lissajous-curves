# Resumen experimento dual

- Modo: `train`
- Webcam CSV: `data/dual_experiments/current_setup/train_20260522_112902/webcam_metrics.csv`
- Frames webcam: `data/dual_experiments/current_setup/train_20260522_112902/webcam_frames`
- Carpeta OP598: `data/dual_experiments/current_setup/train_20260522_112902/op598`

## Webcam

- frames: 335
- detected_frames: 7
- detection_events: 5

## OP598

- baseline_adc: 0.0
- command: sensor train_profile 5 1000 40 1023 40 120 1000
- fall_time_ms: 0.0
- metadata.count: 5
- metadata.duration_ms: 40
- metadata.duty: 1023
- metadata.period_ms: 1000
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 686
- peak_adc: 0.0
- peak_time_ms: 0.123
- pulse_count: 5
- pulse_width_ms: 0.0
- rise_time_ms: 0.0
- sample_count: 686
- sample_interval_avg_ms: 6.135662773722628
- sample_interval_max_ms: 12.634999999999991
- sample_interval_min_ms: 3.646000000000001
- threshold_adc: 0.0
- threshold_crossing_ms: 0.123

## Interpretacion

- El canal OP598 estima detectabilidad y tiempos practicos del sistema LED+sensor+ESP32.
- La webcam aporta evidencia visual y estadistica por frame, no metrologia ultrarapida.
