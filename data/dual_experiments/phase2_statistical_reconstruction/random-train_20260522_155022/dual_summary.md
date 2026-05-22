# Resumen experimento dual

## Idea del metodo

- Este flujo hace reconstruccion estadistica por flashes repetidos, no imagen rapida directa.
- OP598 en ADC36 actua como ancla temporal aproximada.
- La webcam aporta coincidencia visual por frame y artefactos para presentacion.

## Run

- Run ID: `random-train_20260522_155022`
- Modo: `random-train`
- Manifest: `data/dual_experiments/phase2_statistical_reconstruction/random-train_20260522_155022/manifest.json`
- Webcam CSV: `data/dual_experiments/phase2_statistical_reconstruction/random-train_20260522_155022/webcam_metrics.csv`
- Webcam video: `data/dual_experiments/phase2_statistical_reconstruction/random-train_20260522_155022/webcam_capture.avi`
- OP598 dir: `data/dual_experiments/phase2_statistical_reconstruction/random-train_20260522_155022/op598`
- Pulse events: `data/dual_experiments/phase2_statistical_reconstruction/random-train_20260522_155022/pulse_events.csv`
- Coincidencias: `data/dual_experiments/phase2_statistical_reconstruction/random-train_20260522_155022/coincidence_table.csv`

## Webcam

- frames: 785
- detected_frames: 0
- detection_events: 0
- measured_fps: 30.07

## Coincidencia

- pulsos OP598: 10
- pulsos con deteccion webcam en ventana: 0
- pulsos cuyo frame emparejado quedo detectado: 0
- offset medio frame-ancla (ms): -2.5249634991268977
- offset absoluto medio (ms): 8.479276099933486
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

- baseline_adc: 2838.1428571428573
- command: sensor random_train_profile 10 1800 2100 40 32 40 120 1000
- fall_time_ms: 39.64300000000003
- metadata.count: 10
- metadata.duration_ms: 40
- metadata.duty: 32
- metadata.host_capture_finished_perf_counter_s: 9202.653840645
- metadata.host_capture_finished_wall_time_s: 1779483046.399519205
- metadata.host_command_sent_perf_counter_s: 9185.166244973
- metadata.host_command_sent_wall_time_s: 1779483028.911923647
- metadata.max_period_ms: 2100
- metadata.min_period_ms: 1800
- metadata.post_ms: 120
- metadata.pre_ms: 40
- metadata.sample_us: 1000
- metadata.samples: 2628
- peak_adc: 3949.0
- peak_time_ms: 11388.803
- pulse_count: 10
- pulse_width_ms: 11338.018
- rise_time_ms: 0.0
- sample_count: 2628
- sample_interval_avg_ms: 6.6404971450323576
- sample_interval_max_ms: 14.384000000000015
- sample_interval_min_ms: 3.645000000000003
- threshold_adc: 3393.5714285714284
- threshold_crossing_ms: 54.705
