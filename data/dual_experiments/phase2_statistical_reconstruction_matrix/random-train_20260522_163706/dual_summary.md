# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_163706`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_163706/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_163706/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_163706/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_163706/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_163706/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_163706/coincidence_table.csv`

## Webcam

- frames: 780
- detected_frames: 23
- detection_events: 18
- measured_fps: 29.87

## Coincidencia

- pulsos OP598: 10
- pulsos con deteccion webcam en ventana: 10
- pulsos cuyo frame emparejado quedo detectado: 10
- offset medio frame-ancla (ms): 32.111677700595465
- offset absoluto medio (ms): 32.111677700595465
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

- baseline_adc: 2545.8571428571427
- command: sensor random_train_profile 10 1800 2100 40 32 40 120 1000
- fall_time_ms: 
- metadata.count: 10
- metadata.duration_ms: 40
- metadata.duty: 32
- metadata.host_capture_finished_perf_counter_s: 12007.337436375
- metadata.host_capture_finished_wall_time_s: 1779485851.083114386
- metadata.host_command_sent_perf_counter_s: 11989.254853997
- metadata.host_command_sent_wall_time_s: 1779485833.000534296
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 2716
- peak_adc: 3905.0
- peak_time_ms: 15928.329
- pulse_count: 10
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 2716
- sample_interval_avg_ms: 6.646203683241252
- sample_interval_max_ms: 16.045999999999935
- sample_interval_min_ms: 3.6500000000000004
- threshold_adc: 3225.4285714285716
- threshold_crossing_ms: 
