# Resumen de estudio: barrido de parámetros webcam

## Hallazgos
- La exposición muestra comportamiento útil pero no estrictamente monótono en el régimen de duty bajo; el sistema todavía es sensible al umbral y al muestreo discreto por frames.
- La duración del pulso sí muestra una tendencia más clara: pulsos de `5-20 ms` quedan mayormente invisibles para la webcam en estas condiciones, mientras que a partir de `50-100 ms` la detectabilidad mejora.

## Agregado por exposición
| duty | exposure | replicates | mean_detection_probability | bounded_detected_total | detected_total_events | expected_total_pulses |
| --- | --- | --- | --- | --- | --- | --- |
| 6 | 3.0 | 1 | 1.0 | 3 | 3 | 3 |
| 6 | 5.0 | 1 | 1.0 | 3 | 6 | 3 |
| 6 | 10.0 | 1 | 1.0 | 3 | 4 | 3 |
| 6 | 20.0 | 1 | 1.0 | 3 | 3 | 3 |
| 6 | 40.0 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 1.0 | 1 | 0.666667 | 2 | 2 | 3 |
| 8 | 3.0 | 1 | 0.0 | 0 | 0 | 3 |
| 8 | 5.0 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 10.0 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 20.0 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 40.0 | 1 | 1.0 | 3 | 3 | 3 |

## Agregado por duración
| duty | duration_ms | replicates | mean_detection_probability | bounded_detected_total | detected_total_events | expected_total_pulses |
| --- | --- | --- | --- | --- | --- | --- |
| 6 | 5 | 1 | 0.0 | 0 | 0 | 3 |
| 6 | 10 | 1 | 0.0 | 0 | 0 | 3 |
| 6 | 20 | 1 | 0.0 | 0 | 0 | 3 |
| 6 | 30 | 1 | 0.333333 | 1 | 1 | 3 |
| 6 | 40 | 1 | 0.0 | 0 | 0 | 3 |
| 6 | 50 | 1 | 0.333333 | 1 | 1 | 3 |
| 6 | 75 | 1 | 0.666667 | 2 | 2 | 3 |
| 6 | 100 | 1 | 0.0 | 0 | 0 | 3 |
| 6 | 200 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 5 | 1 | 0.0 | 0 | 0 | 3 |
| 8 | 10 | 1 | 0.0 | 0 | 0 | 3 |
| 8 | 20 | 1 | 0.0 | 0 | 0 | 3 |
| 8 | 50 | 1 | 0.666667 | 2 | 2 | 3 |
| 8 | 100 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 200 | 1 | 1.0 | 3 | 3 | 3 |
| 8 | 300 | 1 | 1.0 | 3 | 3 | 3 |

## Limitaciones
- Este estudio mezcla al menos dos duties (`6` y `8`), así que exposición y duración deben leerse condicionadas por duty, no como una curva global única.
- Cada condición también tiene solo `3` pulsos esperados, así que la granularidad de probabilidad es gruesa (`0`, `1/3`, `2/3`, `1`).
- En algunos casos `detection_events` crudo supera los pulsos comandados por sobre-segmentación; la probabilidad se acota usando `min(eventos, pulsos esperados)`.