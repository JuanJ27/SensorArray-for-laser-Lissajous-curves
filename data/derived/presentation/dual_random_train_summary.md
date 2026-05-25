# Resumen de estudio: coincidencia dual random-train

## Hallazgos
- La coincidencia dual ya es cuantificable corrida por corrida usando las ventanas reconstruidas alrededor del ancla OP598.
- Corridas con cobertura webcam incompleta: `1` de `11`.
- La mejor corrida cubierta alcanzó `p=1.0` en `run random-train_20260522_162947`.

## Resumen global
| subset | run_count | mean_windowed_success_rate | mean_all_pulse_success_rate |
| --- | --- | --- | --- |
| all_runs | 11 | 0.475758 | 0.449242 |
| fully_covered_runs | 10 | 0.49 | 0.49 |

## Corridas por run
| run_id | variant | command_count | covered_pulses | coverage_fraction | matched_detected | coincidence_success_rate_windowed | mean_offset_ms_detected | limited_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random-train_20260522_154927 | phase2_statistical_reconstruction | 10 | 10 | 1.0 | 0 | 0.0 |  | false |
| random-train_20260522_155022 | phase2_statistical_reconstruction | 10 | 10 | 1.0 | 0 | 0.0 |  | false |
| random-train_20260522_155311 | phase2_statistical_reconstruction_matrix | 10 | 10 | 1.0 | 5 | 0.5 | -14.849808 | false |
| random-train_20260522_155351 | phase2_statistical_reconstruction_matrix | 10 | 10 | 1.0 | 6 | 0.6 | 19.335576 | false |
| random-train_20260522_155431 | phase2_statistical_reconstruction_matrix | 10 | 10 | 1.0 | 0 | 0.0 |  | false |
| random-train_20260522_162539 | phase2_statistical_reconstruction_matrix | 120 | 15 | 0.125 | 5 | 0.333333 | -41.594841 | true |
| random-train_20260522_162947 | phase2_statistical_reconstruction_matrix | 10 | 10 | 1.0 | 10 | 1.0 | 39.397036 | false |
| random-train_20260522_163706 | phase2_statistical_reconstruction_matrix | 10 | 10 | 1.0 | 10 | 1.0 | 32.111678 | false |
| random-train_20260522_172025 | phase2_statistical_reconstruction_matrix | 10 | 10 | 1.0 | 10 | 1.0 | 39.444915 | false |
| random-train_20260522_155151 | phase2_statistical_reconstruction_probe | 5 | 5 | 1.0 | 0 | 0.0 |  | false |
| random-train_20260522_155230 | phase2_statistical_reconstruction_probe | 5 | 5 | 1.0 | 4 | 0.8 | -10.927491 | false |

## Limitaciones
- Varias corridas largas terminan con cobertura webcam parcial; en esos casos la tasa sobre todos los pulsos subestima la coincidencia real porque el video no cubrió toda la secuencia.
- Los offsets deben interpretarse sobre pulsos detectados o sobre ventanas cubiertas; promedios globales heredados pueden quedar sesgados por frames faltantes al final.