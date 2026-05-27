# Reconstruccion estadistica del evento

## Que es esta reconstruccion

- Es una reconstruccion estadistica por coincidencias repetidas entre el ancla temporal OP598 y frames webcam cercanos.
- NO es video de alta velocidad ni imagen directa de un solo destello resuelta frame a frame.
- El panel comparativo agrega fases `before -> approach -> hit -> decay -> after` tanto en pooled como por corrida.

## Criterio de seleccion de corridas

1. Priorizar cobertura webcam completa (`limited_coverage=false`).
2. Priorizar mayor tasa de coincidencia en ventanas cubiertas.
3. Desempatar por cantidad de pulsos emparejados y por la variante `phase2_statistical_reconstruction_matrix`.
4. Usar recencia solo como ultimo desempate entre corridas equivalentes.

Pulsos acumulados en la reconstruccion: `60`.
ESS pooled entre corridas: `1.00`.
Coincidencia pooled: `1.000` con IC95% `[0.940, 1.000]`.

## Corridas elegidas

|   selection_rank | run_id                       | variant          |   covered_pulses |   matched_detected |   coincidence_success_rate_windowed |   mean_offset_ms_detected |
|-----------------:|:-----------------------------|:-----------------|-----------------:|-------------------:|------------------------------------:|--------------------------:|
|                1 | random-train_20260526_165547 | dual_experiments |               60 |                 60 |                                   1 |                   45.0868 |

## Ranking completo

| run_id                       | variant          |   coverage_fraction |   matched_detected |   coincidence_success_rate_windowed | selected_for_reconstruction   | selection_reason                                                                          |
|:-----------------------------|:-----------------|--------------------:|-------------------:|------------------------------------:|:------------------------------|:------------------------------------------------------------------------------------------|
| random-train_20260526_165547 | dual_experiments |                   1 |                 60 |                            1        | True                          | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses;selected_for_aggregate |
| random-train_20260526_165322 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_165057 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_164832 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_164608 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_164119 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_163854 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_163629 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_163403 | dual_experiments |                   1 |                 60 |                            1        | False                         | full_video_coverage;perfect_windowed_coincidence;10_matched_pulses                        |
| random-train_20260526_164343 | dual_experiments |                   1 |                 59 |                            0.983333 | False                         | full_video_coverage;10_matched_pulses                                                     |

## Artefactos generados

- `avg_flash_frame.png`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/avg_flash_frame.png`
- `flash_heatmap.png`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/flash_heatmap.png`
- `reconstruction_comparison_panel.png`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/reconstruction_comparison_panel.png`
- `coincidence_offset_distribution.png`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/coincidence_offset_distribution.png`
- `reconstruction_statistics.csv`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/reconstruction_statistics.csv`
- `reconstruction_confidence_notes.md`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/reconstruction_confidence_notes.md`
- `reconstruction_uncertainty_summary.md`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/reconstruction_uncertainty_summary.md`
- `pulse_strips/`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/pulse_strips`
- `slowmo_frames/`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/slowmo_frames`
- `slowmo_reconstruction.gif`: `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10/slowmo_reconstruction.gif`

## Lectura cuantitativa minima

- `reconstruction_statistics.csv` resume por corrida y por fase: cantidad de frames, ESS, tasa de coincidencia con IC95%, offset medio y diferencia de brillo contra `before`.
- El panel comparativo permite ver si la fase `hit` se mantiene visualmente entre corridas o si una sola corrida domina el pooled.
- El histograma/boxplot de offsets permite ver si el anclaje temporal es consistente o si la reconstruccion junta eventos con offsets muy distintos.

## Supuestos del metodo

- El tiempo OP598 se usa como ancla temporal aproximada, no como timing fino sub-milisegundo.
- El frame `0` relativo es el frame webcam ya emparejado por la tabla de coincidencia existente.
- Los previews normalizados mejoran interpretabilidad visual, pero no agregan precision radiometrica.

## Lo que SI permite afirmar

- Que existe un patron visual repetible cuando se apilan muchas coincidencias buenas.
- Que ahora hay respaldo cuantitativo minimo para esa narrativa: conteos, ESS, IC95%, offsets y comparacion pooled vs por corrida.
- Que la reconstruccion sirve como proxy visual de evento para presentacion offline.

## Lo que NO permite afirmar

- No prueba imagen directa del flash con resolucion temporal fina.
- No separa por completo la contribucion del LED, la optica, el rolling/integration de la webcam y el timing grueso del OP598.
- La propagacion de incertidumbre incluida es por intervalos y sensibilidad practica, no una calibracion metrologica completa.

## Resumen de incertidumbre

- Duty detectable condicionado: `practical conditional threshold is about duty 6-8, not a single exact duty, because the first success point has limited replicates and low-duty exposure response is non-monotonic`
- Umbral practico de duracion detectable: `practical webcam detectability starts around 50-100 ms depending on duty and exposure, with no evidence for a stable sub-50 ms threshold in the current dataset`
- Offset medio con incertidumbre temporal: `45.1 +/- 20.1 ms from interval-based propagation of mean frame half-period and OP598 half sample-interval`

## Reproducibilidad

```bash
python scripts/build_statistical_reconstruction.py
python scripts/build_uncertainty_summary.py
```

Todos los outputs se escriben en `data/derived/reconstruction-camera0/new-camera-mount-20260526-camera0-extra10`.
