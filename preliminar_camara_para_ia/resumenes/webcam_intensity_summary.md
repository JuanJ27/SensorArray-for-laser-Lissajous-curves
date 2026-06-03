# Resumen de estudio: barrido de intensidad webcam

## Hallazgos
- El mejor promedio de deteccion en esta familia fue `p=0.133334` en `duty 8`.

## Tabla agregada por duty
| duty | replicates | mean_detection_probability | median_detection_probability | bounded_detected_total | detected_total_events | expected_total_pulses |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 3 | 0.0 | 0.0 | 0 | 0 | 180 |
| 1 | 3 | 0.0 | 0.0 | 0 | 0 | 180 |
| 2 | 3 | 0.0 | 0.0 | 0 | 0 | 180 |
| 3 | 3 | 0.0 | 0.0 | 0 | 0 | 180 |
| 4 | 3 | 0.077778 | 0.066667 | 14 | 14 | 180 |
| 5 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 6 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 7 | 3 | 0.122222 | 0.116667 | 22 | 22 | 180 |
| 8 | 3 | 0.133334 | 0.116667 | 24 | 24 | 180 |
| 10 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 12 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 16 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 24 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 32 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 48 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 64 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |
| 128 | 3 | 0.116667 | 0.116667 | 21 | 21 | 180 |

## Limitaciones
- Cada duty agrega `180` pulsos esperados según `led_ack`. La probabilidad usa eventos detectados acotados por pulsos esperados; no identifica qué pulso individual disparó cada detección.
- La métrica es detectabilidad de la cadena webcam + umbral actual, no radiometría del LED.