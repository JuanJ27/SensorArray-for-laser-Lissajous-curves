# Resumen experimento dual

- Modo: `random-train`
- Webcam CSV: `data/dual_experiments/current_setup_fixed/random-train_20260522_113049/webcam_metrics.csv`
- Frames webcam: `data/dual_experiments/current_setup_fixed/random-train_20260522_113049/webcam_frames`
- Carpeta OP598: `data/dual_experiments/current_setup_fixed/random-train_20260522_113049/op598`

## Webcam

- frames: 780
- detected_frames: 13
- detection_events: 10

## OP598

- baseline_adc: 0.0
- command: sensor random_train_profile 10 1800 2100 40 1023 40 120 1000
- fall_time_ms: 
- metadata.count: 10
- metadata.duration_ms: 40
- metadata.duty: 1023
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 2809
- peak_adc: 0.0
- peak_time_ms: 0.111
- pulse_count: 10
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 2809
- sample_interval_avg_ms: 6.329111823361823
- sample_interval_max_ms: 16.06999999999971
- sample_interval_min_ms: 3.6479999999999997
- threshold_adc: 
- threshold_crossing_ms: 

## Interpretacion

- El canal OP598 estima detectabilidad y tiempos practicos del sistema LED+sensor+ESP32.
- La webcam aporta evidencia visual y estadistica por frame, no metrologia ultrarapida.
