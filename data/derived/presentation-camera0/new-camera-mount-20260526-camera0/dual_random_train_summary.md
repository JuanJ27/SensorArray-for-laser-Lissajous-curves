# Resumen de estudio: coincidencia dual random-train

## Hallazgos
- La coincidencia dual ya es cuantificable corrida por corrida usando las ventanas reconstruidas alrededor del ancla OP598.
- Corridas con cobertura webcam incompleta: `0` de `10`.
- La mejor corrida cubierta alcanzó `p=1.0` en `run random-train_20260526_155231`.

## Resumen global
| subset | run_count | mean_windowed_success_rate | mean_all_pulse_success_rate |
| --- | --- | --- | --- |
| all_runs | 10 | 1.0 | 1.0 |
| fully_covered_runs | 10 | 1.0 | 1.0 |

## Corridas por run
| run_id | variant | command_count | covered_pulses | coverage_fraction | matched_detected | coincidence_success_rate_windowed | mean_offset_ms_detected | limited_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random-train_20260526_155231 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 47.777769 | false |
| random-train_20260526_155455 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 48.803207 | false |
| random-train_20260526_155719 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 47.944955 | false |
| random-train_20260526_155943 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 54.367538 | false |
| random-train_20260526_160207 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 49.497447 | false |
| random-train_20260526_160431 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 48.320788 | false |
| random-train_20260526_160655 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 46.447234 | false |
| random-train_20260526_160919 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 53.411653 | false |
| random-train_20260526_161144 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 49.2702 | false |
| random-train_20260526_161408 | dual_experiments | 60 | 60 | 1.0 | 60 | 1.0 | 49.655601 | false |

## Limitaciones
- Varias corridas largas terminan con cobertura webcam parcial; en esos casos la tasa sobre todos los pulsos subestima la coincidencia real porque el video no cubrió toda la secuencia.
- Los offsets deben interpretarse sobre pulsos detectados o sobre ventanas cubiertas; promedios globales heredados pueden quedar sesgados por frames faltantes al final.