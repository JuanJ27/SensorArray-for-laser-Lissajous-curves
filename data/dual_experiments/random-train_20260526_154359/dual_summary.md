# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_154359`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_154359/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_154359/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_154359/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_154359/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_154359/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_154359/coincidence_table.csv`

## Webcam

- frames: 3376
- detected_frames: 0
- detection_events: 0
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): -444.2296192860037
- offset absoluto medio (ms): 450.44162321767845
- ventana usada: 100.0 ms

## Artefactos visuales

- representative_frames: 60
- average_frame_written: True
- heatmap_written: True
- pulse_strip_written: True

## Limites actuales

- El timing del OP598 bajo MicroPython sigue limitado por una cadencia real de ~6.4-6.6 ms.
- La alineacion final sigue siendo por coincidencia estadistica entre un ancla numerica y frames de ~30 FPS.
- Si el OP598 ve un pulso y la webcam no, eso describe sensibilidad distinta entre canales; no invalida el metodo.

## OP598

- baseline_adc: 2299.8571428571427
- command: sensor random_train_profile 60 1800 2200 40 0 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 0
- metadata.host_capture_finished_perf_counter_s: 173858.379155348
- metadata.host_capture_finished_wall_time_s: 1779828365.395788193
- metadata.host_command_sent_perf_counter_s: 173739.555114007
- metadata.host_command_sent_wall_time_s: 1779828246.571749926
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17803
- peak_adc: 2423.0
- peak_time_ms: 0.107
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17803
- sample_interval_avg_ms: 6.671561229075385
- sample_interval_max_ms: 16.175000000000068
- sample_interval_min_ms: 3.6230000000000047
- threshold_adc: 2361.4285714285716
- threshold_crossing_ms: 
