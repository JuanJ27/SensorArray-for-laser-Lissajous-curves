# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_164832`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_164832/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_164832/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_164832/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_164832/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_164832/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_164832/coincidence_table.csv`

## Webcam

- frames: 4093
- detected_frames: 77
- detection_events: 60
- measured_fps: 29.87

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 60
- pulsos cuyo frame emparejado quedo detectado: 60
- offset medio frame-ancla (ms): 51.688866586967684
- offset absoluto medio (ms): 51.688866586967684
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

- baseline_adc: 602.7142857142857
- command: sensor random_train_profile 60 1800 2200 40 1023 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 1023
- metadata.host_capture_finished_perf_counter_s: 177730.259733346
- metadata.host_capture_finished_wall_time_s: 1779832237.276370764
- metadata.host_command_sent_perf_counter_s: 177612.348352730
- metadata.host_command_sent_wall_time_s: 1779832119.364993334
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17618
- peak_adc: 4095.0
- peak_time_ms: 47.066
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17618
- sample_interval_avg_ms: 6.6899545325537835
- sample_interval_max_ms: 16.495999999999185
- sample_interval_min_ms: 3.6340000000000146
- threshold_adc: 2348.8571428571427
- threshold_crossing_ms: 
