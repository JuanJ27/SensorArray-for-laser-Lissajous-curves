# Resumen de estudio: caracterización OP598

## Hallazgos
- El intervalo de muestreo efectivo del camino OP598 se mantiene alrededor de `6.726 ms`, lejos del `1 ms` solicitado.
- Hay saturación clara en duties altos: `128, 512, 1023`.
- El rango bajo (`duty 8-32`) es el más interpretable para comparar amplitud sin pegarse inmediatamente al techo ADC.

## Agregado por duración a duty 1023
| duration_ms | replicates | mean_peak_adc | mean_pulse_width_ms | any_saturated |
| --- | --- | --- | --- | --- |
| 30 | 1 | 4095.0 | 27.538 | true |
| 100 | 1 | 4095.0 | 100.147 | true |
| 200 | 1 | 4095.0 | 206.311 | true |
| 400 | 1 | 4095.0 | 400.594 | true |

## Agregado por duty a duración 200 ms
| duty | replicates | mean_peak_adc | mean_peak_minus_baseline | all_saturated | any_saturated |
| --- | --- | --- | --- | --- | --- |
| 8 | 1 | 3307.0 | 326.153846 | false | false |
| 32 | 1 | 3915.0 | 935.923077 | false | false |
| 128 | 1 | 4095.0 | 1177.0 | true | true |
| 512 | 1 | 4095.0 | 1234.846154 | true | true |
| 1023 | 1 | 4095.0 | 1182.307692 | true | true |

## Limitaciones
- Esto caracteriza la cadena montada `LED + optica + OP598 + ADC + MicroPython`; no es una medición intrínseca ultrarrápida del fototransistor.
- Las corridas saturadas sirven para detectabilidad, pero NO para inferir linealidad de intensidad.