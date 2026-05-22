# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_155351`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155351/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155351/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155351/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155351/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155351/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155351/coincidence_table.csv`

## Webcam

- frames: 785
- detected_frames: 77
- detection_events: 61
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 10
- pulsos con deteccion webcam en ventana: 6
- pulsos cuyo frame emparejado quedo detectado: 6
- offset medio frame-ancla (ms): 8.024082099473162
- offset absoluto medio (ms): 26.543269099602185
- ventana usada: 100.0 ms

## Artefactos visuales

- representative_frames: 10
- average_frame_written: True
- heatmap_written: True
- pulse_strip_written: True

## Limites actuales

- El timing del OP598 bajo MicroPython sigue limitado por una cadencia real de ~6.4-6.6 ms.
- La alineacion final sigue siendo por coincidencia estadistica entre un ancla numerica y frames de ~30 FPS.
- Si el OP598 ve un pulso y la webcam no, eso describe sensibilidad distinta entre canales; no invalida el metodo.

## OP598

- baseline_adc: 2851.8571428571427
- command: sensor random_train_profile 10 1800 2100 40 8 40 120 1000
- fall_time_ms: 
- metadata.count: 10
- metadata.duration_ms: 40
- metadata.duty: 8
- metadata.host_capture_finished_perf_counter_s: 9411.828445823
- metadata.host_capture_finished_wall_time_s: 1779483255.574123621
- metadata.host_command_sent_perf_counter_s: 9394.429942425
- metadata.host_command_sent_wall_time_s: 1779483238.175621033
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 2614
- peak_adc: 3293.0
- peak_time_ms: 13468.637
- pulse_count: 10
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 2614
- sample_interval_avg_ms: 6.639988518943743
- sample_interval_max_ms: 14.408999999999992
- sample_interval_min_ms: 3.6469999999999985
- threshold_adc: 3072.4285714285716
- threshold_crossing_ms: 
