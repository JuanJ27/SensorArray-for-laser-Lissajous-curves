# Resumen de estudio: barrido de intensidad webcam

## Hallazgos
- La webcam empieza a mostrar deteccion consistente desde `duty 6` en estas corridas heredadas.
- El mejor promedio de deteccion en esta familia fue `p=1.0` en `duty 6`.

## Tabla agregada por duty
| duty | replicates | mean_detection_probability | median_detection_probability | bounded_detected_total | detected_total_events | expected_total_pulses |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 0.0 | 0.0 | 0 | 0 | 3 |
| 2 | 1 | 0.0 | 0.0 | 0 | 0 | 3 |
| 4 | 1 | 0.0 | 0.0 | 0 | 0 | 3 |
| 6 | 1 | 1.0 | 1.0 | 3 | 3 | 3 |
| 8 | 3 | 1.0 | 1.0 | 9 | 9 | 9 |
| 10 | 1 | 1.0 | 1.0 | 3 | 3 | 3 |
| 12 | 1 | 1.0 | 1.0 | 3 | 3 | 3 |
| 16 | 3 | 1.0 | 1.0 | 9 | 9 | 9 |
| 24 | 3 | 1.0 | 1.0 | 9 | 9 | 9 |
| 32 | 3 | 1.0 | 1.0 | 9 | 9 | 9 |
| 48 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 64 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 96 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 128 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 192 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 256 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 384 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 512 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 768 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |
| 1023 | 2 | 1.0 | 1.0 | 6 | 6 | 6 |

## Limitaciones
- Estas probabilidades provienen de trenes cortos de `3` pulsos por condición; sirven para comparaciones iniciales, no para estadística final.
- La métrica es detectabilidad de la cadena webcam + umbral actual, no radiometría del LED.