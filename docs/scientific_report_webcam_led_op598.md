# Informe cientifico del sistema webcam + LED + OP598 como análogo controlado de detectabilidad de destellos

## Respuesta corta

El repositorio demuestra una metodologia reproducible para detectar y reconstruir **destellos opticos repetidos** usando una webcam de consumo y un canal analogico OP598 acoplado a un ESP32, pero **no demuestra sonoluminiscencia real**, **no realiza metrologia ultrarapida** y **no convierte a la webcam en una camara de alta velocidad**. El valor cientifico del montaje esta en otro lugar: una estrategia de **coincidencia estadistica entre eventos repetidos**, donde el OP598 aporta un ancla temporal gruesa y la webcam aporta evidencia visual integrada por frame.

La conclusion defendible con la evidencia actual es la siguiente:

| Pregunta | Respuesta defendible |
|---|---|
| ¿Se genero sonoluminiscencia? | No. El sistema usa un LED externo como análogo controlado. |
| ¿La webcam resuelve microdinamica o eventos ultrarrapidos? | No. Opera cerca de `30 FPS` y su lectura esta cuantizada por frame e integracion. |
| ¿El OP598 + ESP32 + MicroPython da timing fino? | No. El muestreo efectivo observado es de aproximadamente `6.4-6.7 ms`, util solo como ancla temporal gruesa. |
| ¿Existe una señal experimental repetible? | Si. Hay detectabilidad reproducible en condiciones adecuadas y coincidencia fuerte en un subconjunto dual seleccionado para reconstruccion. |
| ¿Cual es la metodologia central? | Reconstruccion estadistica a partir de muchas coincidencias repetidas, no observacion directa de un unico flash ultrarapido. |

## Resumen

Este informe documenta el estado experimental del repositorio `/home/juanm/SensorArray-for-laser-Lissajous-curves` para el estudio de detectabilidad de destellos opticos debiles y breves en una caja oscura. El sistema combina una webcam Logitech C525, un LED controlado por ESP32, y un fototransistor OP598 leido por el ADC del ESP32 bajo MicroPython. La motivacion conceptual proviene del problema de observar emisiones luminosas extremadamente breves, como referencia pedagogica hacia fenomenos tipo sonoluminiscencia, pero el montaje actual no reproduce ni mide sonoluminiscencia real.

Los resultados indican que la webcam puede detectar destellos cuando el pulso aporta energia suficiente al frame integrado. En los barridos disponibles, el umbral practico condicionado de detectabilidad aparece alrededor de `duty 6-8` para ciertas configuraciones, y la detectabilidad por duracion mejora claramente hacia `50-100 ms` o mas, con evidencia mas confiable en `200 ms` para condiciones de baja intensidad. El canal OP598 detecta pulsos con claridad, pero satura rapidamente en duties medios y altos, por lo que su utilidad principal en esta etapa no es la fotometria lineal sino el anclaje temporal aproximado y la validacion de coincidencia. En el conjunto dual con cobertura completa, la tasa media de exito por ventana es de `~0.49` (`10` corridas). Dentro de ese universo, el subconjunto de `3` corridas seleccionado para reconstruccion offline alcanzo `30/30` coincidencias sobre ventanas cubiertas, con IC95% de Wilson `[0.886, 1.000]`, y un offset medio entre ancla OP598 y frame webcam emparejado de `~37 +/- 20 ms` bajo una propagacion por intervalos.

La interpretacion correcta es prudente: el sistema demuestra una **cadena experimental de detectabilidad y coincidencia**, no una medicion temporal ultrafina. Su aporte mas fuerte es metodologico y reproducible: mostrar que la informacion visual lenta de una webcam puede combinarse con un sensor optico mas rapido, aunque todavia grosero, para reconstruir estadisticamente un patron de flash repetido.

## Introduccion y motivacion

El problema experimental de este repositorio nace de una tension clasica en medicion optica: algunos eventos luminosos son demasiado breves o demasiado debiles para ser observados de forma directa por instrumentacion de consumo. En un contexto academico, la sonoluminiscencia funciona como motivacion conceptual porque representa precisamente un caso donde el interes cientifico esta ligado a emisiones opticas extremadamente cortas. Sin embargo, ese mismo punto obliga a ser rigurosos: una webcam comun no puede tratarse como sustituto de una camara ultrarapida, y un montaje LED controlado tampoco puede presentarse como sonoluminiscencia real.

La estrategia adoptada por el proyecto evita ese error conceptual. En lugar de reclamar una observacion directa del evento fisico ultrarrapido, el repositorio construye un **análogo controlado de detectabilidad**: un LED externo genera destellos programables dentro de una caja oscura; la webcam mide detectabilidad macroscópica por frame; el OP598 entrega una traza analogica mas rapida, aunque aun limitada; y el analisis offline reconstruye el fenomeno estadistico de coincidencia entre ambos canales.

Esta aproximacion tiene tres virtudes.

1. Permite separar claramente el problema de detectabilidad del problema fisico de sonoluminiscencia.
2. Hace posible validar hardware, firmware y pipeline sin depender de un fenomeno raro o dificil de controlar.
3. Genera un banco de pruebas reproducible para metodos de reconstruccion por coincidencias repetidas.

## Pregunta de investigacion y objetivos

### Pregunta principal

¿Puede una cadena experimental basada en `webcam + LED controlado + OP598 + ESP32` detectar y reconstruir estadisticamente destellos repetidos en una caja oscura bajo limitaciones instrumentales realistas?

### Objetivos especificos

| Objetivo | Criterio practico |
|---|---|
| Evaluar detectabilidad visual con webcam | Medir eventos detectados por frame al variar `duty`, exposicion y duracion. |
| Caracterizar el canal OP598 | Medir baseline, pico, saturacion, ancho de pulso y cadencia efectiva de muestreo. |
| Integrar ambos canales | Construir corridas duales con tablas de coincidencia `OP598 -> webcam`. |
| Evaluar reconstruccion estadistica | Apilar coincidencias repetidas y producir fases promedio `before/approach/hit/decay/after`. |
| Establecer limites honestos | Explicitar incertidumbres, cuantizacion temporal, sensibilidad a umbral y baja cantidad de replicas. |

## Marco teorico

### Motivacion desde la sonoluminiscencia

La sonoluminiscencia es una referencia conceptual util porque plantea el problema de observar emisiones luminosas muy breves y de baja energia relativa. Pero en este proyecto la relacion es solo metodologica. El montaje actual:

- no genera cavitacion controlada,
- no reporta plasma, colapso de burbuja ni emision sonoluminiscente,
- no tiene resolucion temporal compatible con reclamos sobre escalas ultracortas.

Por eso la formulacion correcta es: **análogo controlado del problema de detectabilidad de destellos**, inspirado por la dificultad instrumental que aparece en problemas tipo sonoluminiscencia.

### Limites de las camaras de consumo

Una webcam de consumo integra luz durante cada frame y luego entrega una muestra cuantizada temporalmente por la tasa de cuadros. En el montaje documentado, la Logitech C525 opera cerca de `29.88 FPS`, lo que implica un periodo de frame de aproximadamente `33.47 ms` y una incertidumbre de medio frame de aproximadamente `16.74 ms` en la asociacion temporal mas simple. Esto impone restricciones fuertes.

| Limite | Consecuencia experimental |
|---|---|
| FPS bajo (`~30`) | Pulsos muy cortos pueden caer entre frames. |
| Integracion por exposicion | El detector responde a energia acumulada, no a instante fisico puro. |
| Rolling/integracion de sensor | La forma observada del flash depende de la camara, no solo del evento. |
| Umbral por brillo | La detectabilidad depende de `duty`, duracion, exposicion y ruido. |

### Idea central de coincidencia estadistica en eventos repetidos

La metodologia del repositorio se basa en una idea simple pero potente: si un evento se repite muchas veces y existe un canal auxiliar que lo ancla temporalmente con suficiente consistencia, entonces es posible alinear observaciones visuales lentas y construir una reconstruccion estadistica del patron medio.

En este esquema:

1. El LED produce eventos repetidos y conocidos.
2. El OP598 detecta esos eventos con mejor granularidad temporal que la webcam.
3. La webcam registra una secuencia lenta de frames con evidencia visual parcial.
4. El analisis offline empareja cada pulso con el frame mas cercano dentro de una ventana temporal.
5. Al apilar muchas coincidencias, emerge un promedio visual interpretable.

Esto NO produce video ultrarapido real. Produce una **reconstruccion estadistica condicionada** al mecanismo de emparejamiento y a la calidad del ancla temporal.

## Montaje experimental

### Hardware

| Componente | Implementacion usada | Evidencia principal |
|---|---|---|
| Microcontrolador | ESP32 DevKit v1 con MicroPython | `hardware/led_pulse_controller.py`, `docs/hardware_setup.md` |
| Camara | Logitech C525, indice OpenCV `2` | `docs/webcam_led_flash_experiment.md`, `docs/agent_handoff_webcam_led_flash_experiment.md` |
| Emisor optico | LED externo controlado por PWM en `GPIO17` | `hardware/led_pulse_controller.py` |
| Sensor optico | OP598 en `ADC36` (`verde`) con resistencia de `100kOhm` a GND | `data/op598/op598_characterization_20260522_1524.md` |
| Entorno optico | Caja oscura | `docs/webcam_led_flash_experiment.md`, `data/webcam/flash_experiment_results_20260521*.md` |

### Webcam

La webcam se usa como canal visual de bajo costo y baja velocidad. La configuracion mas repetida en los artefactos es:

| Parametro | Valor habitual |
|---|---|
| Resolucion | `640x480` |
| FPS solicitado | `30` |
| FOURCC | `YUYV` |
| Modo | `--raw` |
| Exposicion | manual, con pruebas en `3, 5, 10, 20, 40` |
| Metrica de deteccion | principalmente `max` |

Su salida fundamental es `webcam_metrics.csv`, con columnas `timestamp_s`, `perf_counter_s`, `frame_index`, `mean`, `max`, `p99`, `threshold`, `detected`.

### ESP32

El ESP32 cumple dos roles.

1. Genera pulsos o trenes de pulsos LED por PWM.
2. Lee el OP598 por ADC durante perfiles simples o corridas duales.

El firmware serial acepta comandos como `pulse`, `train`, `sensor pulse_profile`, `sensor train_profile` y `sensor random_train_profile`, documentados en `docs/webcam_led_flash_experiment.md` y definidos en `hardware/led_pulse_controller.py`.

### LED

El LED experimental esta conectado a `GPIO17` con resistencia limitadora en serie. El parametro de intensidad principal es `duty` en escala `0-1023`, donde `1023` representa el 100% del duty PWM configurado.

### Sensor OP598

El OP598 se alimenta a `3.3V` y su salida se lee en `ADC36`. `docs/hardware_setup.md` se usa aqui solo como contexto de componente y especificacion nominal. Los valores medidos de baseline, saturacion y cadencia temporal usados para interpretar este experimento provienen de `data/op598/op598_characterization_20260522_1524.md`. En la practica, el sistema relevante es `LED + optica + OP598 + resistor + ADC ESP32 + MicroPython + serializacion`, y el repositorio muestra que la cadencia efectiva obtenida fue de aproximadamente `6.4-6.7 ms` por muestra, no `1 ms` ni microsegundos reales.

### Caja oscura

La caja oscura reduce el fondo de luz y vuelve interpretable el detector de umbral. La calidad del baseline oscuro es importante porque la decision `detected=1` depende de superar `baseline + threshold_delta` o el criterio equivalente por `sigma_multiplier`.

### Restricciones conocidas del montaje

| Restriccion | Impacto |
|---|---|
| LED rojo de power de la ESP32 | Debe taparse fisicamente; no se trata como controlable por software. |
| LED onboard en `GPIO2` | Solo se apaga explicitamente con `boardled off`; no se hizo escaneo arbitrario de GPIOs. |
| ADC del ESP32 bajo MicroPython | Agrega jitter y reduce la resolucion temporal efectiva. |
| Saturacion del OP598 a duty alto | Impide interpretar linealmente amplitud en `128, 512, 1023`. |
| Webcam de consumo | Limita severamente la resolucion temporal y la deteccion de pulsos cortos. |

## Adquisicion y pipeline de software

### Firmware

El firmware principal es `hardware/led_pulse_controller.py`. Sus funciones experimentales relevantes son:

| Funcion | Descripcion |
|---|---|
| PWM LED | Control de `duty` y `freq` del LED en `GPIO17`. |
| Pulsos simples | `pulse <duration_ms> <duty>`. |
| Trenes fijos | `train <count> <period_ms> <duration_ms> <duty>`. |
| Trenes aleatorios | `sensor random_train_profile ...` con intervalos variables. |
| Lectura OP598 | Emite `SENSOR_ROW` con `index`, `t_us`, `adc`, `led`, `phase`, `pulse_index`. |

### Herramientas de webcam

La herramienta central es `tools/webcam_flash_detector.py`. El detector:

1. abre la camara,
2. aplica configuracion de resolucion, FPS, FOURCC y controles V4L2,
3. realiza `warmup` y `calibration`,
4. estima baseline y sigma del canal oscuro,
5. calcula un umbral,
6. procesa frame a frame la metrica elegida (`mean`, `max` o `p99`),
7. guarda CSV, video opcional y frames detectados.

### Herramientas de captura OP598

`tools/capture_op598_response.py` ejecuta perfiles simples y guarda:

- CSV crudo de muestras,
- resumen CSV,
- resumen Markdown,
- grafico PNG,
- log de captura.

Ademas calcula metricas como `baseline_adc`, `peak_adc`, `threshold_crossing_ms`, `pulse_width_ms`, `pulse_count` y `sample_interval_avg_ms`.

### Herramientas duales

`tools/run_dual_flash_experiment.py` coordina simultaneamente el detector webcam y la captura OP598. La salida tipica por corrida incluye:

| Artefacto | Funcion |
|---|---|
| `webcam_metrics.csv` | Serie temporal por frame del detector webcam. |
| `webcam_capture.avi` | Grabacion completa de la corrida. |
| `op598/` | CSV, resumenes y plots del canal analogico. |
| `pulse_events.csv` | Eventos de pulso derivados del OP598. |
| `coincidence_table.csv` | Emparejamiento temporal `OP598 -> webcam`. |
| `visuals/` | `average_frame.png`, `coincidence_heatmap.png`, `pulse_strip.png`. |
| `manifest.json` | Metadatos y ubicaciones de la corrida. |
| `dual_summary.csv` y `dual_summary.md` | Resumen cuantitativo final. |

### Pipeline offline de analisis

El repositorio incluye una capa de analisis reproducible sin hardware activo.

| Capa | Archivo principal | Rol |
|---|---|---|
| Catalogacion | `scripts/build_run_catalog.py` | Descubre corridas y valida artefactos. |
| Normalizacion legacy | `scripts/normalize_legacy_runs.py` | Conserva datos heredados sin modificar crudos. |
| Estudios derivados | `data/derived/studies/*.csv` | Resume detectabilidad webcam y caracterizacion OP598. |
| Reconstruccion | `scripts/build_statistical_reconstruction.py` | Selecciona corridas y genera promedios por fase. |
| Incertidumbre | `scripts/build_uncertainty_summary.py` | Resume IC, offsets y sensibilidad a umbrales. |

## Organizacion de datos y validacion

La organizacion de datos esta documentada en `docs/analysis_pipeline.md` y `docs/analysis_data_model.md`. Las familias principales son:

| Ruta | Contenido |
|---|---|
| `data/webcam/` | Corridas webcam puras, sweep de intensidad y parametros. |
| `data/op598/` | Corridas de caracterizacion OP598. |
| `data/dual_experiments/` | Corridas duales webcam + OP598. |
| `data/derived/studies/` | Tablas agregadas para analisis comparativo. |
| `data/derived/reconstruction/` | Productos de reconstruccion estadistica e incertidumbre. |

Los estados de validacion explicitados por el pipeline incluyen `valid`, `partial`, `schema_mismatch`, `missing_artifact`, `legacy_unstructured` e `invalid_empty`. Esta decision es cientificamente sana porque evita inventar datos faltantes y mantiene separados los artefactos plenamente utilizables de los heredados o incompletos.

## Metodologia

Antes de separar resultados, conviene fijar los parametros que gobiernan la reconstruccion dual reportada:

| Parametro | Valor usado en las corridas seleccionadas | Fuente |
|---|---|---|
| Ventana de coincidencia | `100 ms` | `manifest.json` de las corridas seleccionadas |
| Metrica webcam | `max` | `manifest.json` de las corridas seleccionadas |
| Regla de umbral webcam | `detected=1` si la metrica supera baseline mas `threshold_delta`, con `sigma_multiplier=1.0` | `tools/webcam_flash_detector.py`, `manifest.json` |
| Threshold reportado en corridas seleccionadas | `threshold_delta=4` | `manifest.json` de las corridas seleccionadas |
| Run IDs seleccionados | `random-train_20260522_172025`, `random-train_20260522_163706`, `random-train_20260522_162947` | `data/derived/reconstruction/reconstruction_overview.md` |
| Criterio de seleccion | Cobertura webcam completa, mayor coincidencia por ventana; desempate por pulsos emparejados y variante `phase2_statistical_reconstruction_matrix` | `data/derived/reconstruction/reconstruction_overview.md` |

### 1. Ensayos webcam-only

Los ensayos webcam-only buscaron medir detectabilidad visual al variar:

- intensidad PWM (`duty`),
- exposicion de la camara,
- duracion del pulso.

La logica experimental es condicional: un pulso se considera detectable si la metrica del frame supera el umbral definido respecto del baseline oscuro. En las corridas duales usadas para reconstruccion, la metrica principal fue `max` y el criterio operativo fue baseline mas `threshold_delta`, con `sigma_multiplier=1.0`.

### 2. Caracterizacion OP598

La caracterizacion OP598 evaluo:

- baseline oscuro,
- amplitud y pico ADC,
- ancho de pulso aparente,
- saturacion a distintos duties,
- trenes repetidos y su separabilidad,
- cadencia real de muestreo frente a la solicitada.

### 3. Ensayos duales con tren aleatorio

Los ensayos duales mas relevantes son los de `random-train`, donde el periodo entre pulsos varia aleatoriamente en el rango `1800-2100 ms`. Esto evita que una coincidencia aparente sea solo un efecto de phase lock simple con la camara. En este contexto, el OP598 ancla cada pulso y la webcam aporta el frame visual mas cercano dentro de una ventana de `100 ms`.

### 4. Reconstruccion estadistica

La reconstruccion offline NO usa todas las corridas duales por igual. Selecciona un subconjunto con cobertura webcam completa y mejor tasa de coincidencia por ventana; en empate, prioriza mayor cantidad de pulsos emparejados y la variante `phase2_statistical_reconstruction_matrix`. Sobre ese subconjunto extrae frames en offsets relativos `-2, -1, 0, +1, +2` alrededor del frame emparejado, y produce fases promedio:

| Offset | Etiqueta |
|---|---|
| `-2` | `before` |
| `-1` | `approach` |
| `0` | `hit` |
| `+1` | `decay` |
| `+2` | `after` |

El resultado es una visualizacion promedio de evento repetido, no una pelicula real de alta velocidad.

## Resultados

### Detectabilidad webcam vs duty

La evidencia principal proviene de:

- `data/webcam/flash_experiment_results_20260521.md`
- `data/webcam/flash_experiment_results_20260521_additional.md`
- `data/derived/studies/webcam_intensity_by_duty.csv`
- `data/derived/presentation/webcam_intensity_summary.md`

Resultados agregados principales:

| Duty | Replicas | Probabilidad media de deteccion | Observacion |
|---|---:|---:|---|
| `1` | 1 | `0.0` | No detectado |
| `2` | 1 | `0.0` | No detectado |
| `4` | 1 | `0.0` | No detectado |
| `6` | 1 | `1.0` | Primer exito observado; `3/3` pulsos |
| `8` | 3 | `1.0` | Deteccion consistente en dataset actual |
| `16-1023` | 2 a 3 | `1.0` | Detectabilidad alta en condiciones probadas |

Interpretacion rigurosa:

- El primer punto exitoso aparece en `duty=6`, equivalente a `0.59%` del rango PWM.
- Eso NO autoriza a afirmar un umbral exacto en `6`.
- La formulacion defendible, consistente con `reconstruction_uncertainty_summary.md`, es que el **umbral practico condicionado** esta alrededor de `duty 6-8` para este montaje y estos parametros de exposicion y umbral.

### Detectabilidad webcam vs duracion y exposicion

Evidencia principal:

- `data/derived/studies/webcam_parameter_by_duration.csv`
- `data/derived/studies/webcam_parameter_by_exposure.csv`
- `data/derived/presentation/webcam_parameter_summary.md`

Resultados por duracion:

| Duty | Duracion | Replicas | Probabilidad media |
|---|---:|---:|---:|
| `6` | `5 ms` | 1 | `0.0` |
| `6` | `10 ms` | 1 | `0.0` |
| `6` | `20 ms` | 1 | `0.0` |
| `6` | `30 ms` | 1 | `0.333` |
| `6` | `50 ms` | 1 | `0.333` |
| `6` | `75 ms` | 1 | `0.667` |
| `6` | `100 ms` | 1 | `0.0` |
| `6` | `200 ms` | 1 | `1.0` |
| `8` | `50 ms` | 1 | `0.667` |
| `8` | `100-300 ms` | 1 | `1.0` |

Resultados por exposicion:

| Duty | Exposicion | Replicas | Probabilidad media | Nota |
|---|---:|---:|---:|---|
| `6` | `3, 5, 10, 20, 40` | 1 | `1.0` | Hubo sobre-segmentacion en `5` y `10` |
| `8` | `1` | 1 | `0.667` | Exito parcial |
| `8` | `3` | 1 | `0.0` | Falla puntual |
| `8` | `5, 10, 20, 40` | 1 | `1.0` | Deteccion completa |

Interpretacion rigurosa:

- La duracion muestra una tendencia mas clara que la exposicion.
- No hay evidencia estable de deteccion sub-`50 ms` en el dataset actual.
- La exposicion en regime de duty bajo es util pero no monotona.
- La sobre-segmentacion de eventos obliga a reportar detectabilidad acotada por `min(eventos, pulsos esperados)` para no sobreinterpretar conteos brutos.

### Caracterizacion OP598 y saturacion

Evidencia principal:

- `data/op598/op598_characterization_20260522_1524.md`
- `data/derived/studies/op598_characterization_by_duty.csv`
- `data/derived/studies/op598_characterization_by_duration.csv`
- `data/derived/presentation/op598_characterization_summary.md`

Resultados por duty a `200 ms`:

| Duty | Pico medio ADC | Pico - baseline | Saturado |
|---|---:|---:|---|
| `8` | `3307` | `326.15` | No |
| `32` | `3915` | `935.92` | No |
| `128` | `4095` | `1177.0` | Si |
| `512` | `4095` | `1234.85` | Si |
| `1023` | `4095` | `1182.31` | Si |

Resultados por duracion a `duty 1023`:

| Duracion | Pico medio ADC | Ancho medio de pulso | Saturado |
|---|---:|---:|---|
| `30 ms` | `4095` | `27.538 ms` | Si |
| `100 ms` | `4095` | `100.147 ms` | Si |
| `200 ms` | `4095` | `206.311 ms` | Si |
| `400 ms` | `4095` | `400.594 ms` | Si |

Hallazgos clave:

- El baseline no esta clavado en cero; en la corrida de caracterizacion se reporto media cercana a `2973.55` ADC con rango `2899-3141`.
- El OP598 detecta pulsos sin dificultad en el regime iluminado.
- El canal satura muy pronto en duties altos, por lo que no es linealmente interpretable alli.
- La zona mas util para comparaciones de amplitud en este montaje es aproximadamente `duty 8-32`.
- El intervalo de muestreo efectivo observado es cercano a `6.4-6.6 ms`, muy lejos del `1000 us` solicitado.

### Hallazgos de coincidencia dual

Evidencia principal:

- `data/derived/studies/dual_random_train_overall.csv`
- `data/derived/studies/dual_random_train_runs.csv`

Resumen global:

| Subconjunto | Corridas | Tasa media de exito por ventana | Tasa media de exito sobre todos los pulsos |
|---|---:|---:|---:|
| `all_runs` | 11 | `~0.48` | `~0.45` |
| `fully_covered_runs` | 10 | `0.49` | `0.49` |

Lectura correcta de este bloque:

- El desempeno dual global con cobertura completa es intermedio, alrededor de `0.49`.
- El reclamo de `30/30` NO describe ese promedio global; describe solo el subconjunto seleccionado para reconstruccion.

Corridas seleccionadas para reconstruccion:

| Run ID | Variante | Pulsos cubiertos | Coincidencia por ventana | Offset medio detectado |
|---|---|---:|---:|---:|
| `random-train_20260522_162947` | `phase2_statistical_reconstruction_matrix` | 10 | `1.0` | `~39.4 ms` |
| `random-train_20260522_163706` | `phase2_statistical_reconstruction_matrix` | 10 | `1.0` | `~32.1 ms` |
| `random-train_20260522_172025` | `phase2_statistical_reconstruction_matrix` | 10 | `1.0` | `~39.4 ms` |

Tambien hay corridas con desempeno pobre o nulo, por ejemplo:

- `random-train_20260522_154927`: coincidencia `0.0`.
- `random-train_20260522_155022`: coincidencia `0.0`.
- `random-train_20260522_155431`: coincidencia `0.0`.

Esto es importante cientificamente: el metodo NO funciona de manera trivial en cualquier configuracion; depende de parametros y calidad de cobertura.

### Salidas de reconstruccion estadistica

Evidencia principal:

- `data/derived/reconstruction/reconstruction_overview.md`
- `data/derived/reconstruction/reconstruction_statistics.csv`
- `data/derived/reconstruction/reconstruction_confidence_notes.md`
- `data/derived/reconstruction/reconstruction_uncertainty_summary.md`

Resultado pooled del subconjunto seleccionado para reconstruccion:

| Magnitud | Valor |
|---|---|
| Corridas seleccionadas | `3` |
| Pulsos acumulados | `30` |
| ESS entre corridas | `3.00` |
| Coincidencia pooled en ventanas cubiertas | `30/30 = 1.000` |
| IC95% Wilson | `[0.886, 1.000]` |
| Offset medio del frame emparejado | `~37 ms` |

Cambios medios de brillo por fase en `reconstruction_statistics.csv`:

| Fase | `delta_mean_gray_vs_before` | Lectura |
|---|---:|---|
| `before` | `0.000000` | Baseline pooled |
| `approach` | `0.000000` | Sin aumento medio claro |
| `hit` | `~0.038` | Incremento medio de brillo coherente con el flash emparejado |
| `decay` | `~0.009` | Persistencia debil posterior |
| `after` | `0.000000` | Retorno al baseline |

Interpretacion:

- El mayor contraste pooled aparece en la fase `hit`.
- La fase `decay` conserva un incremento menor pero positivo.
- La reconstruccion es visualmente interpretable y cuantitativamente consistente con la narrativa de un flash repetido.
- Sin embargo, el contraste absoluto es pequeno; por lo tanto la lectura debe apoyarse en repeticion, no en espectacularidad visual de un solo frame.

## Errores sistematicos e incertidumbre

### Cuantizacion por frame rate

La webcam opera cerca de `29.88 FPS`, equivalente a periodos de aproximadamente `33.47 ms`. El resumen de incertidumbre reporta una semianchura temporal de medio frame de aproximadamente `16.74 ms`. Este termino domina cualquier reclamo de precision temporal asociado solo al canal webcam.

### Cadencia gruesa del OP598

Aunque el firmware permite pedir `sample_us=1000`, la caracterizacion muestra una cadencia efectiva promedio cercana a `6.6 ms`. Eso hace que el OP598 sea un **ancla temporal gruesa** y no un instrumento de timing fino. El propio repositorio lo reconoce en `data/op598/op598_characterization_20260522_1524.md` y `data/derived/reconstruction/reconstruction_uncertainty_summary.md`.

### Sensibilidad al umbral

Los resultados dependen del criterio de deteccion. En webcam, el umbral se construye desde baseline y `threshold_delta` o `sigma_multiplier`. En el barrido de baja intensidad, `threshold-delta=20` y `30` detectaron `duty=6`, mientras `40` no detecto nada. La sensibilidad offline reportada en `data/derived/reconstruction/threshold_sensitivity.csv` muestra que, para las corridas seleccionadas, aumentar el margen de matched-frame en `+10%` y `+20%` retuvo `30/30` coincidencias. Esto aporta robustez local, pero no reemplaza una recalibracion completa del detector.

### Falsos positivos y falsos negativos no cuantificados con dark-control dedicado

El pipeline incluye baselines oscuros y corridas de referencia, pero en el dataset actual no se ejecuto una campana dedicada de control oscuro prolongado para estimar tasas de falsos positivos y falsos negativos de extremo a extremo. Por eso la interpretacion estadistica de detectabilidad y coincidencia sigue siendo util, pero todavia incompleta desde el punto de vista de caracterizacion formal del detector.

### Saturacion

El OP598 alcanza techo ADC (`4095`) en `duty 128, 512, 1023`. Por lo tanto:

- esas corridas sirven para discutir presencia o coincidencia,
- no sirven para inferir linealidad de intensidad,
- cualquier interpretacion de amplitud en ese regimen debe evitarse.

### Pocas replicas

Gran parte de las condiciones en `data/derived/studies/` tiene entre `1` y `3` replicas, y a veces solo un tren corto de `3` pulsos por condicion. Esto impone granularidad grosera en probabilidad (`0`, `1/3`, `2/3`, `1`) y obliga a formular conclusiones como rangos practicos, no como umbrales fisicos precisos.

### Incertidumbre propagada e interpretacion por intervalos

El repositorio adopta una estrategia razonable: usar IC binomiales exactos o Wilson cuando corresponde, y limites por intervalos cuando una propagacion gaussiana fina no es defendible. El resultado sintetico mas importante es:

| Magnitud | Declaracion defendible |
|---|---|
| Coincidencia pooled del subconjunto seleccionado | `30/30 = 1.000`, IC95% Wilson `[0.886, 1.000]` |
| Offset medio | `~37 +/- 20 ms` por propagacion basada en medio frame webcam y media muestra OP598 |
| Umbral de duty | Aproximadamente `6-8`, no un valor exacto unico |
| Umbral de duracion webcam | Aproximadamente `50-100 ms` segun duty y exposicion; sin evidencia estable sub-`50 ms` |

## Discusion

### Que es cientificamente significativo

Lo mas fuerte del sistema actual no es la rapidez instrumental aislada, sino la coherencia metodologica entre adquisicion y analisis.

Son aportes cientificamente significativos dentro del alcance actual:

1. Haber separado claramente el problema de detectabilidad del reclamo de sonoluminiscencia real.
2. Haber cuantificado la detectabilidad webcam en funcion de intensidad, exposicion y duracion.
3. Haber mostrado que el OP598 detecta pulsos y permite anclaje temporal util, aunque grosero.
4. Haber construido una pipeline dual reproducible con tablas de coincidencia y reconstruccion offline.
5. Haber acompañado las mejores coincidencias con IC95%, ESS y notas explicitas de incertidumbre.

### Que es solo practico o instrumental

Tambien hay resultados utiles pero de valor principalmente instrumental:

- tapar el LED rojo de power de la ESP32,
- apagar explicitamente el LED onboard conocido en `GPIO2`,
- usar `metric=max` para un LED pequeño,
- fijar exposicion manual y desactivar `exposure-auto-priority`,
- preferir el rango `duty 8-32` para caracterizacion OP598 no saturada.

Estos puntos son claves para reproducir el sistema, pero no deben confundirse con descubrimientos fisicos sobre el fenomeno modelado.

### Lo que el montaje puede y no puede demostrar

| Reclamo | Estado |
|---|---|
| Que la cadena experimental detecta destellos repetidos | Si |
| Que existe coincidencia reproducible entre canal analogico y webcam | Si, en un subconjunto seleccionado de las mejores corridas |
| Que una webcam comun registra directamente la microdinamica del flash | No |
| Que el OP598 bajo MicroPython hace metrologia ultrarapida | No |
| Que el sistema observa sonoluminiscencia real | No |
| Que la reconstruccion equivale a video de alta velocidad | No |

## Conclusiones

1. El repositorio implementa un experimento reproducible y tecnicamente coherente para estudiar **detectabilidad de destellos opticos repetidos** en una caja oscura.
2. El sistema debe describirse como un **análogo controlado**, no como sonoluminiscencia real.
3. La webcam Logitech C525 aporta evidencia visual de baja velocidad; detecta de forma confiable cuando el pulso y la exposicion le entregan suficiente energia integrada, pero no resuelve eventos ultrarrapidos.
4. El canal OP598 mejora la validacion temporal respecto de la webcam sola, pero su cadena real de muestreo bajo ESP32 + MicroPython entrega resolucion del orden de milisegundos, no submilisegundos.
5. La metodologia central y defendible es la **reconstruccion estadistica por coincidencias repetidas**, apoyada por tablas duales, corridas seleccionadas, IC95% y sensibilidad a umbrales.
6. En `10` corridas duales con cobertura completa, la tasa media de exito por ventana es de `~0.49`; dentro de ese conjunto, el subconjunto de `3` corridas seleccionado para reconstruccion muestra una coincidencia pooled de `30/30` sobre ventanas cubiertas con IC95% `[0.886, 1.000]`.
7. Las conclusiones sobre umbral de intensidad y duracion deben formularse como **rangos practicos condicionales**, debido a la baja cantidad de replicas y a la dependencia de parametros.

## Trabajo futuro

| Prioridad | Trabajo | Motivo cientifico |
|---|---|---|
| Alta | Aumentar replicas por condicion | Reducir incertidumbre y evitar umbrales basados en una sola corrida. |
| Alta | Barridos duales sistematicos en `duty`, `duration`, `exposure`, `threshold` | Mapear region de operacion util del sistema completo. |
| Alta | Migrar adquisicion OP598 a Arduino/C++ o ESP-IDF si se requiere mejor timing | Reducir overhead de MicroPython y mejorar cadencia real. |
| Media | Definir ROI fija y calibrada para webcam | Bajar ruido espacial y hacer el detector mas estable. |
| Media | Estimar falsos positivos y falsos negativos en corridas largas oscuras | Fortalecer interpretacion estadistica del detector. |
| Media | Repetir reconstruccion con mas corridas comparables | Mejorar ESS y estabilidad inter-corrida. |
| Baja | Incorporar calibracion radiometrica o control de intensidad optica real | Separar mejor detectabilidad de simple PWM nominal. |

## Apéndice de reproducibilidad

### Comandos clave

Preparacion basica:

```bash
cd /home/juanm/SensorArray-for-laser-Lissajous-curves
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Carga de firmware:

```bash
ampy --port /dev/ttyUSB0 put hardware/led_pulse_controller.py main.py
ampy --port /dev/ttyUSB0 reset
```

Detector webcam:

```bash
python tools/webcam_flash_detector.py \
  --index 2 \
  --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --seconds 8 --warmup 1 --calibration 3
```

Corrida integrada webcam + LED:

```bash
python tools/run_led_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --count 5 --period-ms 1000 --duration-ms 300 --duty 1023
```

Caracterizacion OP598:

```bash
python tools/capture_op598_response.py \
  --port /dev/ttyUSB0 \
  pulse --duration-ms 40 --duty 1023 --pre-ms 40 --post-ms 120 --sample-us 1000
```

Corrida dual estadistica:

```bash
python tools/run_dual_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 20 --exposure-auto-priority 0 \
  --metric max --threshold-delta 4 --sigma-multiplier 1.0 \
  --coincidence-window-ms 100 \
  random-train --count 10 --min-period-ms 1800 --max-period-ms 2100 \
  --duration-ms 40 --duty 32 --pre-ms 40 --post-ms 120 --sample-us 1000
```

Reconstruccion offline:

```bash
python scripts/build_statistical_reconstruction.py
python scripts/build_uncertainty_summary.py
```

### Rutas de salida clave

| Ruta | Contenido |
|---|---|
| `data/webcam/` | CSV de detector webcam y reportes Markdown base. |
| `data/op598/` | CSV, plots y resumenes OP598. |
| `data/dual_experiments/` | Corridas duales completas con manifest y coincidencias. |
| `data/derived/studies/` | Tablas agregadas para intensidad, exposicion, duracion y corridas duales. |
| `data/derived/reconstruction/` | Reconstruccion estadistica, paneles, GIF y resumenes de incertidumbre. |
| `data/derived/presentation/` | Resumenes y figuras de apoyo para presentacion. |

## Referencias internas y archivos de evidencia

### Documentacion principal

- `docs/webcam_led_flash_experiment.md`
- `docs/agent_handoff_webcam_led_flash_experiment.md`
- `docs/analysis_pipeline.md`
- `docs/analysis_data_model.md`
- `docs/legacy_normalization.md`
- `docs/presentation_storyline.md`
- `docs/hardware_setup.md`

### Resultados fuente

- `data/webcam/flash_experiment_results_20260521.md`
- `data/webcam/flash_experiment_results_20260521_additional.md`
- `data/op598/op598_characterization_20260522_1524.md`

### Tablas derivadas

- `data/derived/studies/webcam_intensity_by_duty.csv`
- `data/derived/studies/webcam_parameter_by_duration.csv`
- `data/derived/studies/webcam_parameter_by_exposure.csv`
- `data/derived/studies/op598_characterization_by_duty.csv`
- `data/derived/studies/op598_characterization_by_duration.csv`
- `data/derived/studies/dual_random_train_overall.csv`
- `data/derived/studies/dual_random_train_runs.csv`

### Reconstruccion e incertidumbre

- `data/derived/reconstruction/reconstruction_overview.md`
- `data/derived/reconstruction/reconstruction_statistics.csv`
- `data/derived/reconstruction/reconstruction_confidence_notes.md`
- `data/derived/reconstruction/reconstruction_uncertainty_summary.md`
- `data/derived/reconstruction/threshold_sensitivity.csv`
- `data/derived/reconstruction/reconstruction_comparison_panel.png`
- `data/derived/reconstruction/avg_flash_frame.png`
- `data/derived/reconstruction/flash_heatmap.png`
- `data/derived/reconstruction/slowmo_reconstruction.gif`

### Herramientas y firmware relevantes

- `hardware/led_pulse_controller.py`
- `tools/webcam_flash_detector.py`
- `tools/run_led_flash_experiment.py`
- `tools/capture_op598_response.py`
- `tools/run_dual_flash_experiment.py`
- `scripts/build_statistical_reconstruction.py`
- `scripts/build_uncertainty_summary.py`

## Caveats finales

- Este informe sintetiza la mejor evidencia disponible en el repositorio a la fecha, pero varias conclusiones siguen siendo exploratorias por bajo numero de replicas.
- Los resultados de detectabilidad deben leerse siempre condicionados por exposicion, umbral, geometria optica y configuracion del LED.
- La reconstruccion estadistica es metodologicamente valiosa, pero no debe presentarse como sustituto de instrumentacion de alta velocidad cuando la pregunta cientifica requiera resolucion temporal fina.
