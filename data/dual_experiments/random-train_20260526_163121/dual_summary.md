# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_163121`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_163121/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_163121/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_163121/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_163121/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_163121/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_163121/coincidence_table.csv`

## Webcam

- frames: 4093
- detected_frames: 0
- detection_events: 0
- measured_fps: 29.87

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): -0.8967208627533788
- offset absoluto medio (ms): 8.248240018535094
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

- baseline_adc: 2600.285714285714
- command: sensor random_train_profile 60 1800 2200 40 0 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 0
- metadata.host_capture_finished_perf_counter_s: 176701.225222792
- metadata.host_capture_finished_wall_time_s: 1779831208.241856575
- metadata.host_command_sent_perf_counter_s: 176581.586353643
- metadata.host_command_sent_wall_time_s: 1779831088.602989197
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17904
- peak_adc: 2722.0
- peak_time_ms: 0.106
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17904
- sample_interval_avg_ms: 6.679787465787856
- sample_interval_max_ms: 16.48300000000745
- sample_interval_min_ms: 3.6499999999999986
- threshold_adc: 2661.142857142857
- threshold_crossing_ms: 
