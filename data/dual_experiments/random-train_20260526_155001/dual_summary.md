# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_155001`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_155001/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_155001/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_155001/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_155001/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_155001/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_155001/coincidence_table.csv`

## Webcam

- frames: 4096
- detected_frames: 0
- detection_events: 0
- measured_fps: 29.89

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): -1.8551207506485905
- offset absoluto medio (ms): 9.14156056533102
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

- baseline_adc: 2413.1428571428573
- command: sensor random_train_profile 60 1800 2200 40 0 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 0
- metadata.host_capture_finished_perf_counter_s: 174219.901909469
- metadata.host_capture_finished_wall_time_s: 1779828726.918548584
- metadata.host_command_sent_perf_counter_s: 174101.598700499
- metadata.host_command_sent_wall_time_s: 1779828608.615336180
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17731
- peak_adc: 2538.0
- peak_time_ms: 0.115
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17731
- sample_interval_avg_ms: 6.669794416243655
- sample_interval_max_ms: 15.779999999998836
- sample_interval_min_ms: 3.655000000000001
- threshold_adc: 2475.5714285714284
- threshold_crossing_ms: 
