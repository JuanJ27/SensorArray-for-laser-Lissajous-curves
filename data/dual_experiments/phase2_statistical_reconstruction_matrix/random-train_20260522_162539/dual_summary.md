# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_162539`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_162539/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_162539/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_162539/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_162539/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_162539/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_162539/coincidence_table.csv`

## Webcam

- frames: 904
- detected_frames: 36
- detection_events: 34
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 120
- pulsos con deteccion webcam en ventana: 5
- pulsos cuyo frame emparejado quedo detectado: 5
- offset medio frame-ancla (ms): -90422.95497177383
- offset absoluto medio (ms): 90423.81985572386
- ventana usada: 100.0 ms

## Artefactos visuales

- representative_frames: 120
- average_frame_written: True
- heatmap_written: True
- pulse_strip_written: True

## Limites actuales

- El timing del OP598 bajo MicroPython sigue limitado por una cadencia real de ~6.4-6.6 ms.
- La alineacion final sigue siendo por coincidencia estadistica entre un ancla numerica y frames de ~30 FPS.
- Si el OP598 ve un pulso y la webcam no, eso describe sensibilidad distinta entre canales; no invalida el metodo.

## OP598

- baseline_adc: 2868.1428571428573
- command: sensor random_train_profile 120 1800 2100 40 32 40 120 1000
- fall_time_ms: 
- metadata.count: 120
- metadata.duration_ms: 40
- metadata.duty: 32
- metadata.host_capture_finished_perf_counter_s: 11535.445651238
- metadata.host_capture_finished_wall_time_s: 1779485379.191328764
- metadata.host_command_sent_perf_counter_s: 11302.520096055
- metadata.host_command_sent_wall_time_s: 1779485146.265776873
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 33417
- peak_adc: 3945.0
- peak_time_ms: 88067.312
- pulse_count: 120
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 33417
- sample_interval_avg_ms: 6.968733570744553
- sample_interval_max_ms: 16.197000000000116
- sample_interval_min_ms: 3.6389999999999993
- threshold_adc: 3406.5714285714284
- threshold_crossing_ms: 
