# Resumen experimento dual

- Modo: `random-train`
- Webcam CSV: `data/dual_experiments/current_setup/random-train_20260522_112745/webcam_metrics.csv`
- Frames webcam: `data/dual_experiments/current_setup/random-train_20260522_112745/webcam_frames`
- Carpeta OP598: `data/dual_experiments/current_setup/random-train_20260522_112745/op598`

## Webcam

- frames: 780
- detected_frames: 0
- detection_events: 0

## OP598

- baseline_adc: 0.0
- command: sensor random_train_profile 10 1800 2100 40 1023 40 120 1000
- fall_time_ms: 0.0
- metadata.count: 10
- metadata.duration_ms: 40
- metadata.duty: 1023
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 2862
- peak_adc: 0.0
- peak_time_ms: 0.111
- pulse_count: 10
- pulse_width_ms: 0.0
- rise_time_ms: 0.0
- sample_count: 2862
- threshold_adc: 0.0
- threshold_crossing_ms: 0.111

## Interpretacion

- El canal OP598 estima detectabilidad y tiempos practicos del sistema LED+sensor+ESP32.
- La webcam aporta evidencia visual y estadistica por frame, no metrologia ultrarapida.
