# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_160431`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_160431/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_160431/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_160431/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_160431/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_160431/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_160431/coincidence_table.csv`

## Webcam

- frames: 4093
- detected_frames: 77
- detection_events: 60
- measured_fps: 29.87

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 60
- pulsos cuyo frame emparejado quedo detectado: 60
- offset medio frame-ancla (ms): 48.3207884724834
- offset absoluto medio (ms): 48.3207884724834
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

- baseline_adc: 609.0
- command: sensor random_train_profile 60 1800 2200 40 1023 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 1023
- metadata.host_capture_finished_perf_counter_s: 175089.014276741
- metadata.host_capture_finished_wall_time_s: 1779829596.030910969
- metadata.host_command_sent_perf_counter_s: 174971.241186615
- metadata.host_command_sent_wall_time_s: 1779829478.257822752
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17604
- peak_adc: 4095.0
- peak_time_ms: 46.744
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17604
- sample_interval_avg_ms: 6.687808271317389
- sample_interval_max_ms: 15.986000000004424
- sample_interval_min_ms: 3.6500000000000004
- threshold_adc: 2352.0
- threshold_crossing_ms: 
