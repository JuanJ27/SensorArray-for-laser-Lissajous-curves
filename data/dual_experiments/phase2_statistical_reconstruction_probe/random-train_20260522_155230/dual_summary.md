# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_155230`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155230/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155230/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155230/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155230/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155230/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155230/coincidence_table.csv`

## Webcam

- frames: 470
- detected_frames: 94
- detection_events: 65
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 5
- pulsos con deteccion webcam en ventana: 4
- pulsos cuyo frame emparejado quedo detectado: 4
- offset medio frame-ancla (ms): -7.02936360030435
- offset absoluto medio (ms): 28.2274684002914
- ventana usada: 100.0 ms

## Artefactos visuales

- representative_frames: 5
- average_frame_written: True
- heatmap_written: True
- pulse_strip_written: True

## Limites actuales

- El timing del OP598 bajo MicroPython sigue limitado por una cadencia real de ~6.4-6.6 ms.
- La alineacion final sigue siendo por coincidencia estadistica entre un ancla numerica y frames de ~30 FPS.
- Si el OP598 ve un pulso y la webcam no, eso describe sensibilidad distinta entre canales; no invalida el metodo.

## OP598

- baseline_adc: 2907.5714285714284
- command: sensor random_train_profile 5 1800 2100 40 32 40 120 1000
- fall_time_ms: 
- metadata.count: 5
- metadata.duration_ms: 40
- metadata.duty: 32
- metadata.host_capture_finished_perf_counter_s: 9321.132438046
- metadata.host_capture_finished_wall_time_s: 1779483164.878116608
- metadata.host_command_sent_perf_counter_s: 9312.970419743
- metadata.host_command_sent_wall_time_s: 1779483156.716098547
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 1229
- peak_adc: 3873.0
- peak_time_ms: 46.395
- pulse_count: 5
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 1229
- sample_interval_avg_ms: 6.608411237785015
- sample_interval_max_ms: 12.785000000000082
- sample_interval_min_ms: 3.6130000000000564
- threshold_adc: 3390.285714285714
- threshold_crossing_ms: 
