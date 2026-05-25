# Modelo canonico minimo

## Run

Una fila en `runs_catalog.csv` representa una corrida o un grupo de artefactos relacionados por directorio o prefijo temporal.

Campos principales:

- `run_id`: identificador estable derivado del nombre de carpeta o archivo
- `family`: `webcam`, `op598`, `dual_experiments` o `latency_runs`
- `variant`: subcarpeta relativa dentro de la familia cuando aplica
- `status`: estado agregado de validacion
- `kind`: tipo de agrupacion, por ejemplo `artifact_group` o `run_directory`
- `primary_artifact`: archivo principal para reproducir la lectura posterior

## Validation Row

Una fila en `validation_report.csv` representa la validacion de un artefacto puntual.

Campos principales:

- `artifact_kind`: tipo de artefacto validado
- `artifact_path`: ruta relativa
- `required`: indica si afecta el estado agregado de la corrida
- `status`: resultado de validacion del artefacto
- `schema_ok`: confirma si el encabezado minimo coincide
- `row_count`: cantidad de filas de datos cuando aplica

## Run Summary

Una fila en `run_summaries.csv` resume metadatos minimos ya normalizados.

Ejemplos de campos:

- `mode`
- `pulse_count`
- `webcam_frames`
- `webcam_detected_frames`
- `op598_sample_count`
- `op598_peak_adc`
- `latency_avg_us`

La idea es mantener este CSV chico, determinista y apto para comparaciones futuras sin tener que reabrir manualmente todos los artefactos originales.
