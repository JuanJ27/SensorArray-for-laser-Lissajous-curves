# Capa de analisis reproducible

## Que hace

Esta capa agrega una primera pasada de analisis offline sobre datos ya capturados en el repositorio. No toca hardware, no adquiere nuevas muestras y no modifica el flujo experimental.

Su objetivo es:

- descubrir corridas y artefactos existentes
- validar presencia y esquema basico de los archivos mas importantes
- normalizar metadatos minimos en CSVs derivados reproducibles
- dejar una base clara para humanos y agentes

## Que carpetas escanea

El builder recorre estas familias de datos:

- `data/webcam/`
- `data/op598/`
- `data/dual_experiments/`
- `data/latency_runs/` como familia opcional

### Reglas principales

- En corridas duales usa `manifest.json` cuando existe.
- En `data/op598/` agrupa archivos por prefijo temporal, por ejemplo `op598_sample_20260522_134415.*`.
- En `data/webcam/` trata `webcam_flash_metrics_*.csv` como corridas estructuradas.
- Los CSV heredados que no siguen esos patrones quedan marcados como `legacy_unstructured`.

## Salidas que escribe

Por defecto escribe en `data/derived/catalog/`:

- `runs_catalog.csv`: una fila por corrida o grupo de artefactos
- `validation_report.csv`: una fila por artefacto validado
- `run_summaries.csv`: metadatos minimos normalizados para analisis posterior

La normalizacion legacy escribe salidas adicionales en `data/derived/normalized/`:

- `normalized_runs.csv`: una fila por corrida legacy normalizada o artefacto marcado explicitamente
- `normalization_report.csv`: decisiones de reparacion, inferencia conservadora o descarte reproducible

## Como correrlo

Desde la raiz del repo:

```bash
python scripts/build_run_catalog.py
```

Para aplicar la slice de normalizacion legacy y regenerar catalogo derivado:

```bash
python scripts/normalize_legacy_runs.py
python scripts/build_run_catalog.py
```

Opciones utiles:

```bash
python scripts/build_run_catalog.py --skip-latency
python scripts/build_run_catalog.py --output-dir data/derived/catalog
```

El script imprime un resumen JSON con rutas de salida y conteos.

## Que valida

### Webcam

- `webcam_flash_metrics_*.csv`
- columnas esperadas: `timestamp_s`, `frame_index`, `mean`, `max`, `p99`, `threshold`, `detected`

### OP598

- CSV crudo con columnas: `index`, `t_us`, `t_ms`, `adc`, `led`, `phase`, `pulse_index`
- CSV resumen `_summary.csv` con columnas `field,value`

### Corridas duales

- `dual_summary.csv`
- `webcam_metrics.csv`
- `pulse_events.csv`
- `coincidence_table.csv`
- presencia de `op598/`
- si existe `manifest.json`, se toma como fuente prioritaria de rutas y metadatos

### Latencia opcional

- `*_results_*.csv`
- `*_summary_*.csv`

## Significado de estados

- `valid`: los artefactos requeridos existen y cumplen el esquema minimo esperado
- `partial`: faltan uno o mas artefactos requeridos, pero existe parte de la corrida
- `missing_artifact`: estado a nivel artefacto; el archivo o directorio esperado no existe
- `schema_mismatch`: el archivo existe pero no contiene las columnas minimas esperadas
- `legacy_unstructured`: artefacto heredado o documentacion que no encaja en el modelo estructurado actual
- `invalid_empty`: CSV presente pero vacio; se preservan links a companions si existen, pero no se fabrica medicion

## Politicas de normalizacion legacy

- Corridas duales antiguas con `webcam_metrics.csv` parseable pero sin `perf_counter_s` se aceptan como `partial` si tienen `timestamp_s`; la salida marca `perf_counter_s_inferred_from_timestamp=true`.
- `pulse_events.csv` y `coincidence_table.csv` faltantes no se inventan. La corrida queda `partial` cuando existen `dual_summary.csv`, `webcam_metrics.csv` y `op598/`.
- Sweeps legacy de webcam se agrupan por su columna `csv` cuando todos los CSVs companion existen.
- CSVs vacios de latencia quedan como `invalid_empty` y conservan enlaces a summary/log companion si estan presentes.
- Logs o documentos sueltos sin tabla cruda reproducible quedan como `legacy_unstructured` en el reporte normalizado.

## Limitaciones de esta primera slice

- No intenta reconstruir ciencia experimental nueva.
- No ejecuta notebooks ni analisis numerico pesado.
- No corrige datos; solo cataloga, valida y resume.
- Los CSV heredados fuera de los formatos nuevos se conservan, pero quedan explicitamente etiquetados.

## Limitaciones de la normalizacion legacy

- No reubica archivos ni reorganiza `data/`; todas las salidas son derivadas y aditivas.
- La inferencia de `perf_counter_s` desde `timestamp_s` solo marca compatibilidad de esquema; no agrega precision temporal nueva.
- Los artefactos vacios o sueltos siguen fuera del conjunto analitico valido.
