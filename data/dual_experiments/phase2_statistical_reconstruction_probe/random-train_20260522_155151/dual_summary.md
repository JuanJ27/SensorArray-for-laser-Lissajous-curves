# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_155151`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155151/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155151/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155151/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155151/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155151/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction_probe/random-train_20260522_155151/coincidence_table.csv`

## Webcam

- frames: 470
- detected_frames: 11
- detection_events: 11
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 5
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): 2.503899600560544
- offset absoluto medio (ms): 6.357425200258149
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

- baseline_adc: 2886.8571428571427
- command: sensor random_train_profile 5 1800 2100 40 32 40 120 1000
- fall_time_ms: 
- metadata.count: 5
- metadata.duration_ms: 40
- metadata.duty: 32
- metadata.host_capture_finished_perf_counter_s: 9282.081087104
- metadata.host_capture_finished_wall_time_s: 1779483125.826764822
- metadata.host_command_sent_perf_counter_s: 9274.039272072
- metadata.host_command_sent_wall_time_s: 1779483117.784950733
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 1212
- peak_adc: 3865.0
- peak_time_ms: 7872.731
- pulse_count: 5
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 1212
- sample_interval_avg_ms: 6.61040132122213
- sample_interval_max_ms: 14.388000000000034
- sample_interval_min_ms: 3.6449999999999996
- threshold_adc: 3375.9285714285716
- threshold_crossing_ms: 
