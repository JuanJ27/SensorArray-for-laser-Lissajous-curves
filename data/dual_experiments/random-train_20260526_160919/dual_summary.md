# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_160919`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_160919/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_160919/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_160919/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_160919/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_160919/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_160919/coincidence_table.csv`

## Webcam

- frames: 4093
- detected_frames: 82
- detection_events: 60
- measured_fps: 29.87

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 60
- pulsos cuyo frame emparejado quedo detectado: 60
- offset medio frame-ancla (ms): 53.41165315185208
- offset absoluto medio (ms): 53.41165315185208
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

- baseline_adc: 730.1428571428571
- command: sensor random_train_profile 60 1800 2200 40 1023 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 1023
- metadata.host_capture_finished_perf_counter_s: 175377.529962735
- metadata.host_capture_finished_wall_time_s: 1779829884.546596289
- metadata.host_command_sent_perf_counter_s: 175259.520436811
- metadata.host_command_sent_wall_time_s: 1779829766.537073612
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17629
- peak_adc: 4095.0
- peak_time_ms: 47.866
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17629
- sample_interval_avg_ms: 6.6914986385296125
- sample_interval_max_ms: 16.49099999999453
- sample_interval_min_ms: 3.6479999999999997
- threshold_adc: 2412.5714285714284
- threshold_crossing_ms: 
