# Resumen de estudio: coincidencia dual random-train

## Hallazgos
- La coincidencia dual ya es cuantificable corrida por corrida usando las ventanas reconstruidas alrededor del ancla OP598.
- Corridas con cobertura webcam incompleta: `0` de `10`.
- La mejor corrida cubierta alcanzó `p=1.0` en `run random-train_20260526_163403`.

## Resumen global
| subset | run_count | mean_windowed_success_rate | mean_all_pulse_success_rate |
| --- | --- | --- | --- |
| all_runs | 10 | 0.998333 | 0.998333 |
| fully_covered_runs | 10 | 0.998333 | 0.998333 |

## Corridas por run
| run_id | variant | command_count | covered_pulses | coverage_fraction | matched_detected | coincidence_success_rate_windowed | mean_offset_ms_detected | limited_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random-train_20260526_163403 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 49.94001 | false |
| random-train_20260526_163629 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 45.332412 | false |
| random-train_20260526_163854 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 53.033436 | false |
| random-train_20260526_164119 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 52.069591 | false |
| random-train_20260526_164343 | dual_experiments | 60 | 60 | 1.0 | 59 | 0.983333 | 49.984351 | false |
| random-train_20260526_164608 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 46.791416 | false |
| random-train_20260526_164832 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 51.688867 | false |
| random-train_20260526_165057 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 46.274107 | false |
| random-train_20260526_165322 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 50.968421 | false |
| random-train_20260526_165547 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 45.086826 | false |

## Limitaciones
- Varias corridas largas terminan con cobertura webcam parcial; en esos casos la tasa sobre todos los pulsos subestima la coincidencia real porque el video no cubrió toda la secuencia.
- Los offsets deben interpretarse sobre pulsos detectados o sobre ventanas cubiertas; promedios globales heredados pueden quedar sesgados por frames faltantes al final.