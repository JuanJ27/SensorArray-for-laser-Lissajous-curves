# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_155431`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155431/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155431/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155431/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155431/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155431/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction_matrix/random-train_20260522_155431/coincidence_table.csv`

## Webcam

- frames: 785
- detected_frames: 0
- detection_events: 0
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 10
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): 2.513872799136152
- offset absoluto medio (ms): 8.892935599760676
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

- baseline_adc: 2914.4285714285716
- command: sensor random_train_profile 10 1800 2100 20 32 40 120 1000
- fall_time_ms: 
- metadata.count: 10
- metadata.duration_ms: 20
- metadata.duty: 32
- metadata.host_capture_finished_perf_counter_s: 9451.929662318
- metadata.host_capture_finished_wall_time_s: 1779483295.675339699
- metadata.host_command_sent_perf_counter_s: 9434.109414361
- metadata.host_command_sent_wall_time_s: 1779483277.855094194
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 2676
- peak_adc: 3809.0
- peak_time_ms: 3942.668
- pulse_count: 10
- pulse_width_ms: 
- rise_time_ms: 
- sample_count: 2676
- sample_interval_avg_ms: 6.644730841121495
- sample_interval_max_ms: 14.415999999999997
- sample_interval_min_ms: 3.6609999999999943
- threshold_adc: 3361.714285714286
- threshold_crossing_ms: 
