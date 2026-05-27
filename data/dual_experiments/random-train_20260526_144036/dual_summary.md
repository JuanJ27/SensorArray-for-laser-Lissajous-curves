# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260526_144036`
- Modo: `random-train`
- Manifest: `data/dual_experiments/random-train_20260526_144036/manifest.json`
- Webcam CSV: `data/dual_experiments/random-train_20260526_144036/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/random-train_20260526_144036/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/random-train_20260526_144036/op598`
- Pulse events: `data/dual_experiments/random-train_20260526_144036/pulse_events.csv`
- Coincidencias: `data/dual_experiments/random-train_20260526_144036/coincidence_table.csv`

## Webcam

- frames: 4120
- detected_frames: 0
- detection_events: 0
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 60
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): 0.8641895299660973
- offset absoluto medio (ms): 8.38599083411585
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

- baseline_adc: 2658.285714285714
- command: sensor random_train_profile 60 1800 2200 40 0 40 120 1000
- fall_time_ms: 
- metadata.count: 60
- metadata.duration_ms: 40
- metadata.duty: 0
- metadata.host_capture_finished_perf_counter_s: 170056.487790755
- metadata.host_capture_finished_wall_time_s: 1779824563.504423857
- metadata.host_command_sent_perf_counter_s: 169937.143852790
- metadata.host_command_sent_wall_time_s: 1779824444.160490274
- metadata.max_period_ms: 2200
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 17691
- peak_adc: 2783.0
- peak_time_ms: 0.115
- pulse_count: 60
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 17691
- sample_interval_avg_ms: 6.743197682306389
- sample_interval_max_ms: 16.127000000000407
- sample_interval_min_ms: 3.6479999999999997
- threshold_adc: 2720.642857142857
- threshold_crossing_ms: 
