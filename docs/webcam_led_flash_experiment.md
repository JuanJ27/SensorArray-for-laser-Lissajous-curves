# Experimento minimo: webcam + LED con ESP32

Esta guia deja listo el flujo practico pedido por el profesor: controlar la intensidad del LED, ajustar la exposicion/integracion de la webcam y detectar si hubo un destello dentro de una caja oscura.

## Camino rapido

1. Cubre fisicamente el LED rojo de power de la ESP32 con cinta; no es controlable por software.
2. Carga `hardware/led_pulse_controller.py` en la ESP32 como `main.py`.
3. Conecta el LED experimental con resistencia limitadora al `GPIO 17`.
4. Ejecuta `./scripts/flash_experiment.sh` o los barridos y mide los destellos con la webcam.

## Objetivo

| Requisito | Implementacion preparada |
|-----------|--------------------------|
| Sistema con LED | ESP32 controla un LED por PWM en `GPIO 17`. |
| Cambiar tiempo de integracion | La webcam permite ajustar exposicion con `--auto-exposure manual --exposure <valor>`. |
| Cambiar intensidad del LED | PWM por comando `set duty <0-1023>` o `pulse ... <duty>`. |
| Detectar presencia de destello | `tools/webcam_flash_detector.py` registra intensidad por frame y marca detecciones. |
| Tiempo exacto del evento | Queda como objetivo extendido; el CSV guarda timestamp por frame para analisis posterior. |

## Seguridad de hardware

- No conectes un LED de alta corriente directo al GPIO del ESP32.
- Usa siempre resistencia limitadora en serie con el LED.
- Para un LED comun de prueba, empezar con `220 ohm` a `1 kohm` es razonable.
- Si usas LED potente o modulo laser, usa transistor/MOSFET y fuente externa adecuada.
- Comparte tierra: `GND ESP32` debe estar unido al `GND` del circuito LED.
- Antes de poner el LED dentro de la caja, prueba con duty bajo: `set duty 100`.
- El LED rojo de power de esta ESP32 debe cubrirse con cinta o barrera opaca; normalmente esta conectado a alimentacion y no se puede apagar desde firmware.
- El LED onboard azul conocido esta en `GPIO 2` y en esta placa queda apagado con valor `0`. El firmware solo acepta `boardled off` para ese pin y no escanea ni conmuta otros GPIO.

## Que significa `duty`

`duty` es la intensidad PWM que se le manda al LED en una escala de `0` a `1023`:

| Duty | Intensidad aproximada |
|------|-----------------------|
| `0` | `0.00%`, apagado |
| `8` | `0.78%` |
| `16` | `1.56%` |
| `32` | `3.13%` |
| `64` | `6.26%` |
| `128` | `12.51%` |
| `256` | `25.02%` |
| `512` | `50.05%` |
| `1023` | `100.00%`, maxima intensidad PWM |

Formula usada en los scripts: `intensity_percent = duty / 1023 * 100`.

## Conexion para manana

| Elemento | Conexion |
|----------|----------|
| ESP32 `GPIO 17` | Resistencia limitadora en serie hacia el anodo del LED. |
| Catodo LED | `GND` del ESP32. |
| Webcam C525 | USB a la PC, indice OpenCV `2`. |
| Caja oscura | LED y zona observada dentro de la caja; webcam apuntando al destello. |

Si el LED consume mas de lo que permite un GPIO, no uses esta conexion directa. Usa `GPIO 17 -> resistencia de gate/base -> transistor/MOSFET`, LED con resistencia/fuente aparte y tierra comun.

## Preparar entorno Python

```bash
cd /home/juanm/SensorArray-for-laser-Lissajous-curves
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Prueba de webcam hoy

La C525 util esta en `--index 2`. En la caja oscura, sin LED, el resultado esperado es `Detected frames: 0` o muy pocos falsos positivos si hay ruido/luz externa.

```bash
python tools/webcam_flash_detector.py \
  --index 2 \
  --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --seconds 8 --warmup 1 --calibration 3
```

Para ver la imagen, agrega `--preview`:

```bash
python tools/webcam_flash_detector.py \
  --index 2 \
  --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --seconds 8 --warmup 1 --calibration 3 \
  --preview
```

Para fijar exposicion manual y evitar que poca luz baje el FPS:

```bash
python tools/webcam_flash_detector.py \
  --index 2 \
  --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --seconds 8 --warmup 1 --calibration 3
```

El CSV queda en `data/webcam/webcam_flash_metrics_<fecha>.csv` con columnas:

| Columna | Significado |
|---------|-------------|
| `timestamp_s` | Tiempo local del frame desde el inicio de deteccion. |
| `frame_index` | Numero de frame procesado. |
| `mean` | Intensidad media del ROI. |
| `max` | Pixel mas brillante del ROI. |
| `p99` | Percentil 99 de intensidad; metrica por defecto. |
| `threshold` | Umbral calculado con baseline oscuro. |
| `detected` | `1` si el frame cruza el umbral. |

## Cargar controlador en ESP32

Opcion simple con `ampy`:

```bash
source .venv/bin/activate
ampy --port /dev/ttyUSB0 put hardware/led_pulse_controller.py main.py
ampy --port /dev/ttyUSB0 reset
```

Si el reset con `ampy` no responde, desconecta y reconecta la ESP32.

Comandos que entiende el firmware por serial:

| Comando | Ejemplo | Efecto |
|---------|---------|--------|
| `set duty <0-1023>` | `set duty 300` | Deja el LED encendido con ese PWM. |
| `set freq <hz>` | `set freq 1000` | Cambia frecuencia PWM. |
| `pulse <duration_ms> <duty>` | `pulse 100 800` | Hace un destello y vuelve al duty anterior. |
| `train <count> <period_ms> <duration_ms> <duty>` | `train 5 1000 100 1023` | Genera varios destellos. |
| `off` | `off` | Apaga el LED. |
| `boardled off` | `boardled off` | Apaga el LED integrado azul conocido en `GPIO 2` escribiendo valor `0`. |
| `status` | `status` | Imprime estado machine-readable. |
| `sensor status` | `sensor status` | Estado del OP598 en `ADC36`, canal `verde`. |
| `sensor sample <count> <delay>` | `sensor sample 200 1ms` | Muestra el ADC sin disparar perfiles. |
| `sensor pulse_profile ...` | `sensor pulse_profile 40 1023 40 120 1000` | Baseline + pulso + cola con stream ADC parseable. |
| `sensor train_profile ...` | `sensor train_profile 5 1000 40 1023 40 120 1000` | Tren fijo con stream ADC parseable. |
| `sensor random_train_profile ...` | `sensor random_train_profile 30 1800 2100 40 1023 40 120 1000` | Tren aleatorio para metodología estadística. |

Las respuestas tienen formato como `OK pulse duration_ms=100 duty=800` o `ERR message=...`.
Los perfiles con sensor emiten además líneas `SENSOR_HEADER ...` y `SENSOR_ROW ...`
con `index`, `t_us`, `adc`, `led`, `phase` y `pulse_index`.

## Canal numerico OP598 en ADC36

El montaje nuevo deja al OP598 ya conectado en el canal `verde` sobre `ADC36`.
Ese canal NO reemplaza un osciloscopio, pero sí permite una estimación mucho más
útil que la webcam para ver si la cadena `LED + circuito + sensor + ESP32`
detecta y separa pulsos cortos.

Qué mide este canal:

- Respuesta práctica del sistema iluminado sobre el sensor.
- Nivel baseline, pico, cruce de umbral y ancho detectable del pulso.
- Separación aproximada entre pulsos en trenes repetidos.

Qué NO puede afirmar:

- No es metrología de nanosegundos.
- No aísla la respuesta física pura del OP598.
- `sample_us` es aproximado en MicroPython; `adc.read()` y `print()` agregan latencia y jitter.

## Captura OP598 desde la PC

Estado y baseline simple:

```bash
python tools/capture_op598_response.py --port /dev/ttyUSB0 status
python tools/capture_op598_response.py --port /dev/ttyUSB0 sample --sample-count 200 --sample-delay 1 --sample-unit ms
```

Pulso único con plot guardado:

```bash
python tools/capture_op598_response.py \
  --port /dev/ttyUSB0 \
  --live-plot \
  pulse --duration-ms 40 --duty 1023 --pre-ms 40 --post-ms 120 --sample-us 1000
```

Tren fijo:

```bash
python tools/capture_op598_response.py \
  --port /dev/ttyUSB0 \
  train --count 5 --period-ms 1000 --duration-ms 40 --duty 1023 \
  --pre-ms 40 --post-ms 120 --sample-us 1000
```

Tren aleatorio `1.8-2.1 s`:

```bash
python tools/capture_op598_response.py \
  --port /dev/ttyUSB0 \
  random-train --count 30 --min-period-ms 1800 --max-period-ms 2100 \
  --duration-ms 40 --duty 1023 --pre-ms 40 --post-ms 120 --sample-us 1000
```

La herramienta guarda por corrida:

- CSV con muestras ADC y estado LED en `data/op598/`
- Resumen CSV y Markdown con baseline, pico, cruce de umbral, rise/fall y ancho de pulso
- PNG para presentación
- Plot en vivo si hay display gráfico disponible; si no, hace fallback a guardado + texto

## Runner dual webcam + OP598

Pulso único:

```bash
python tools/run_dual_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --preview \
  --save-detected-frames \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  pulse --duration-ms 40 --duty 1023 --pre-ms 40 --post-ms 120 --sample-us 1000
```

Tren repetido:

```bash
python tools/run_dual_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  train --count 10 --period-ms 1000 --duration-ms 40 --duty 1023 \
  --pre-ms 40 --post-ms 120 --sample-us 1000
```

Método estadístico de coincidencia con intervalos aleatorios oscuros:

```bash
python tools/run_dual_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  random-train --count 30 --min-period-ms 1800 --max-period-ms 2100 \
  --duration-ms 40 --duty 1023 --pre-ms 40 --post-ms 120 --sample-us 1000
```

Salida del runner dual:

- `webcam_metrics.csv`
- `webcam_capture.avi` con la corrida completa de la webcam
- `webcam_frames/` con frames detectados representativos
- carpeta `op598/` con CSV, resumen y plots del canal numerico
- `pulse_events.csv` con anclas y amplitud por pulso derivadas del OP598
- `coincidence_table.csv` con el join `OP598 -> webcam` por ventana temporal
- `visuals/` con `average_frame.png`, `coincidence_heatmap.png`, `pulse_strip.png`
- `manifest.json` con metadata y ubicacion de artefactos
- `dual_summary.csv`
- `dual_summary.md`

Interpretación útil para reconstrucción estadística:

- `pulse_index` y `t_us` del OP598 dan la referencia numérica más confiable de cada disparo dentro de este montaje.
- El CSV webcam permite revisar `before/during/after` por frame y contar coincidencias visuales.
- Si el OP598 detecta pulsos que la webcam no ve, eso NO invalida el experimento: justamente muestra la diferencia entre un canal óptico rápido aproximado y uno visual lento.
- `coincidence_table.csv` es la tabla práctica para presentación: dice qué frame quedó más cerca de cada pulso y si cayó una detección dentro de la ventana elegida.

## Fase dual estadistica actual

Esta fase NO intenta filmar el flash "en tiempo real" como si la webcam fuera rápida.
Lo que hace es otra cosa, y es importante entenderlo bien:

- OP598 en `ADC36` da un ancla temporal gruesa por pulso.
- La webcam a `~30 FPS` aporta coincidencia visual por frame.
- Los intervalos aleatorios `1800-2100 ms` evitan phase lock simple con la cámara.
- La reconstrucción sale de repetir pulsos y acumular evidencia, no de un frame mágico.

Límite actual del canal OP598 bajo esta ruta MicroPython:

- Cadencia real de muestreo: aproximadamente `6.4-6.6 ms` aunque se pida `1000 us`.
- Eso alcanza para anclar pulsos cortos y separar eventos repetidos.
- NO alcanza para reclamar timing fino sub-milisegundo.

Matriz recomendada para correr ahora en este montaje:

```bash
python tools/run_dual_flash_experiment.py \
  --output-dir data/dual_experiments/phase2_statistical_reconstruction_matrix \
  --port /dev/ttyUSB0 \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --save-detected-frames \
  --auto-exposure manual --exposure 20 --exposure-auto-priority 0 \
  --metric max --threshold-delta 4 --sigma-multiplier 1.0 \
  --coincidence-window-ms 100 \
  random-train --count 10 --min-period-ms 1800 --max-period-ms 2100 \
  --duration-ms 40 --duty 32 --pre-ms 40 --post-ms 120 --sample-us 1000

python tools/run_dual_flash_experiment.py \
  --output-dir data/dual_experiments/phase2_statistical_reconstruction_matrix \
  --port /dev/ttyUSB0 \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --save-detected-frames \
  --auto-exposure manual --exposure 20 --exposure-auto-priority 0 \
  --metric max --threshold-delta 4 --sigma-multiplier 1.0 \
  --coincidence-window-ms 100 \
  random-train --count 10 --min-period-ms 1800 --max-period-ms 2100 \
  --duration-ms 40 --duty 8 --pre-ms 40 --post-ms 120 --sample-us 1000

python tools/run_dual_flash_experiment.py \
  --output-dir data/dual_experiments/phase2_statistical_reconstruction_matrix \
  --port /dev/ttyUSB0 \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --save-detected-frames \
  --auto-exposure manual --exposure 20 --exposure-auto-priority 0 \
  --metric max --threshold-delta 4 --sigma-multiplier 1.0 \
  --coincidence-window-ms 100 \
  random-train --count 10 --min-period-ms 1800 --max-period-ms 2100 \
  --duration-ms 20 --duty 32 --pre-ms 40 --post-ms 120 --sample-us 1000
```

Lectura honesta de estos settings:

- Son útiles para coincidencia estadística, NO para detección frame-perfect limpia.
- `exposure=20` y `threshold-delta=4` rescatan coincidencias visuales en la zona útil del OP598, pero agregan falsos positivos.
- Justamente por eso la ventana alrededor del ancla OP598 es parte del método, no un parche cosmético.

## Probar LED desde la PC

```bash
python tools/led_serial_control.py --port /dev/ttyUSB0 status
python tools/led_serial_control.py --port /dev/ttyUSB0 boardled off
python tools/led_serial_control.py --port /dev/ttyUSB0 --duty 100
python tools/led_serial_control.py --port /dev/ttyUSB0 --off
python tools/led_serial_control.py --port /dev/ttyUSB0 --pulse 100 800
python tools/led_serial_control.py --port /dev/ttyUSB0 --train 5 1000 100 1023
```

Verificacion esperada del LED onboard azul:

```bash
python tools/led_serial_control.py --port /dev/ttyUSB0 boardled off
# OK boardled pin=2 state=off value=0

python tools/led_serial_control.py --port /dev/ttyUSB0 status
# OK status duty=0 freq=1000 onboard_led_pin=2 onboard_led_value=0 pin=17
```

## Experimento en dos terminales

Terminal 1, detector:

```bash
python tools/webcam_flash_detector.py \
  --index 2 \
  --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --seconds 20 --warmup 1 --calibration 3 \
  --preview
```

Terminal 2, tren de pulsos despues de que termine la calibracion:

```bash
python tools/led_serial_control.py --port /dev/ttyUSB0 --train 5 1000 100 1023
```

## Runner integrado opcional

Cuando el firmware ya este cargado y el LED conectado:

```bash
python tools/run_led_flash_experiment.py \
  --port /dev/ttyUSB0 \
  --index 2 \
  --raw \
  --auto-exposure manual --exposure 10 --exposure-auto-priority 0 \
  --metric max --threshold-delta 30 \
  --count 5 --period-ms 1000 --duration-ms 300 --duty 1023 \
  --preview \
  --save-detected-frames \
  --frames-dir data/webcam/flash_presentation/demo
```

Este runner arranca el detector, espera warmup + calibracion y luego envia el tren de pulsos. Con `--preview` se ve en pantalla lo que ve la camara. Con `--save-detected-frames` se guardan PNG de los frames detectados para presentacion.

## Comandos comodos

Si tu terminal no deja copiar comandos largos facilmente, usa los scripts listos:

```bash
./scripts/esp32_all_off.sh
./scripts/flash_experiment.sh
./scripts/intensity_sweep.sh
./scripts/flash_parameter_sweep.sh
```

`intensity_sweep.sh` prueba varios valores PWM, abre preview y genera un CSV con el minimo `duty` detectado y su porcentaje equivalente.

`flash_parameter_sweep.sh` ejecuta barridos analogos de detectabilidad: exposicion de camara y duracion de pulso. Tambien abre preview y guarda frames detectados. Esto no crea sonoluminiscencia real; solo imita el problema de detectar destellos breves y debiles con la webcam disponible.

Los PNG quedan bajo `data/webcam/flash_presentation/` separados por tipo de prueba.

## Resultados registrados 2026-05-21

Configuracion comun: Logitech C525 en `--index 2`, `640x480`, `YUYV`, `--raw`,
exposicion manual, `--exposure-auto-priority 0`, metrica `max`,
`--threshold-delta 30`.

| Prueba | Resultado | CSV |
|--------|-----------|-----|
| Tren integrado `5 x 300 ms`, `duty=1023`, periodo `1000 ms` | 46 frames detectados, 5 eventos detectados de 5 pulsos, 29.88 FPS | `data/webcam/webcam_flash_metrics_20260521_114151.csv` |
| Barrido de intensidad `duty=8..1023`, `3 x 200 ms` | Todos los duties probados dieron 3 eventos; minimo detectado probado: `8` | `data/webcam/led_intensity_sweep_20260521_114216.csv` |
| Barrido analogo exposicion/duracion con `duty=8` | Exposicion `3` fallo en esa corrida; `5+` detecto los 3 eventos. Duraciones `5/10/20 ms` no detectadas; `50 ms` detecto 2 eventos; `100+ ms` detecto 3 eventos | `data/webcam/flash_parameter_sweep_20260521_114453.csv` |

Resumen detallado: `data/webcam/flash_experiment_results_20260521.md`.

Resultados adicionales con preview, frames PNG para presentacion, porcentaje de intensidad, barridos de exposicion/duracion y robustez de umbral: `data/webcam/flash_experiment_results_20260521_additional.md`.

## Ajustes utiles

| Problema | Ajuste recomendado |
|----------|--------------------|
| Falsos positivos en oscuridad | Sube `--threshold-delta` o `--sigma-multiplier`. |
| No detecta destellos debiles | Baja `--threshold-delta`, sube `--duty` o usa ROI manual. |
| Mucho ruido fuera del LED | Usa `--roi x,y,w,h` o `--select-roi --preview`. |
| FPS cae en oscuridad | Usa exposicion manual y `--exposure-auto-priority 0`. |
| La preview no abre | Ejecuta sin `--preview`; el CSV igual se genera. |

Para un LED pequeno visto como un punto, usa `--metric max`. `p99` es mas estable
para regiones grandes, pero puede ignorar destellos que ocupan pocos pixeles.

Ejemplo con ROI manual:

```bash
python tools/webcam_flash_detector.py \
  --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --raw \
  --roi 220,140,200,160 \
  --seconds 20 --warmup 1 --calibration 3
```
