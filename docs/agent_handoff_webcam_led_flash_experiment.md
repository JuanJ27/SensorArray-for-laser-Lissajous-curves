# Handoff: experimento webcam + LED con ESP32

Este documento resume el trabajo listo para subir a GitHub y para que otra persona, o un agente de codigo, pueda reproducirlo sin reinterpretar el repo. El experimento usa una Logitech C525 y un ESP32 que controla un LED externo en `GPIO17` para medir detectabilidad de destellos. Es un analogo estadistico de detectabilidad de flashes; no es sonoluminiscencia real.

## Camino rapido

1. Cubrir fisicamente el LED rojo de power de la ESP32 con cinta opaca.
2. Activar el entorno Python e instalar dependencias.
3. Cargar `hardware/led_pulse_controller.py` en la ESP32 como `main.py`.
4. Apagar LED externo y LED onboard conocido.
5. Ejecutar `./scripts/flash_experiment.sh` para demo confiable.
6. Ejecutar `./scripts/intensity_sweep.sh` y `./scripts/flash_parameter_sweep.sh` para barridos.
7. Revisar CSV/PNG en `data/webcam/` y `data/webcam/flash_presentation/`.

## Resumen ejecutivo

| Punto | Estado |
|-------|--------|
| Montaje | Webcam Logitech C525 + ESP32 + LED externo en `GPIO17` dentro de caja oscura. |
| Objetivo | Medir si una webcam comun puede detectar flashes repetidos variando intensidad PWM, exposicion y duracion. |
| Alcance cientifico | Analogo de detectabilidad de destellos; NO genera ni mide sonoluminiscencia real. |
| Camara | Logitech C525 en indice OpenCV `2`, `640x480`, `YUYV`, modo raw. |
| Resultado fuerte | Flujo integrado detecto `5/5` eventos; demo de estabilidad con `duty=512` detecto `10/10`. |
| Limite bajo reciente | Minimo detectable probado: `duty=6/1023 = 0.59%`; `duty=1/2/4` no detectados con `threshold-delta=30`. |

## Que cambio en el repo

| Area | Archivos | Para que sirve |
|------|----------|----------------|
| Herramientas webcam | `tools/webcam_fps_tool.py`, `tools/webcam_flash_detector.py` | Medir FPS real, configurar camara con OpenCV/V4L2 y detectar flashes por frame. |
| Control serial ESP32 | `tools/led_serial_control.py` | Enviar comandos `status`, `off`, `boardled off`, `pulse` y `train` al firmware MicroPython. |
| Runners integrados | `tools/run_led_flash_experiment.py`, `tools/run_led_intensity_sweep.py`, `tools/run_flash_parameter_sweep.py` | Coordinar detector + tren de pulsos y guardar CSV/PNG. |
| Firmware | `hardware/led_pulse_controller.py` | Control PWM del LED externo en `GPIO17`; apaga el LED onboard conocido en `GPIO2`. |
| Scripts | `scripts/esp32_all_off.sh`, `scripts/flash_experiment.sh`, `scripts/intensity_sweep.sh`, `scripts/flash_parameter_sweep.sh` | Comandos cortos para ejecutar el flujo sin copiar lineas largas. |
| Documentacion | `docs/webcam_led_flash_experiment.md`, este handoff | Guia practica y reporte de traspaso. |
| Datos/resultados | `data/webcam/*.csv`, `data/webcam/*results*.md`, `data/webcam/flash_presentation/*` | Evidencia numerica y visual de los experimentos. |

## Supuestos de hardware

| Elemento | Supuesto operativo |
|----------|--------------------|
| Webcam | Logitech C525 en indice OpenCV `2`. |
| Camara/configuracion | `640x480`, `30 FPS` solicitado, `YUYV`, `--raw`, exposicion manual. |
| ESP32 | Puerto serial `/dev/ttyUSB0`, MicroPython. |
| LED externo | Conectado a `GPIO17` mediante resistencia limitadora. |
| Tierra | `GND` del ESP32 compartido con el circuito del LED. |
| LED rojo de power | Debe taparse fisicamente; se trata como no controlable por software. |
| LED onboard controlable | Solo se conoce `GPIO2`; se usa `boardled off`. No se debe hacer escaneo arbitrario de GPIOs. |

## Como ejecutar

Ejecutar desde la raiz del repo:

```bash
cd /home/juanm/SensorArray-for-laser-Lissajous-curves
```

## Gobernanza de campaña (new-camera-mount)

Para evitar mezcla con corridas legacy, cualquier corrida de producción del nuevo
montaje debe cumplir:

- `campaign_id` explícito y consistente durante todo el lote.
- `mount_context=new-camera-mount`.
- `run_intent=dark-control` para la corrida de control oscuro y `run_intent=production` para el lote.
- `dark_control_ref` obligatorio en cada corrida productiva.
- Freshness del dark-control: máximo **5 minutos** antes de la primera corrida productiva.

El primer lote aceptado para reconstrucción estadística se define como:

- **10 corridas independientes** (`run_index` 1..10).
- **120 s** por corrida.
- Intervalo aleatorio entre flashes de **1.8 a 2.2 s**.

Si falta metadata o falla gate de dark-control, el lote no es elegible para
reconstrucción y se debe corregir/repetir.

### 1. Preparar entorno Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Cargar firmware en la ESP32

```bash
source .venv/bin/activate
ampy --port /dev/ttyUSB0 put hardware/led_pulse_controller.py main.py
ampy --port /dev/ttyUSB0 reset
```

Si `ampy reset` no responde, desconectar y reconectar la ESP32.

### 3. Apagar todo antes de medir

```bash
./scripts/esp32_all_off.sh
```

Equivalente manual:

```bash
python tools/led_serial_control.py --port /dev/ttyUSB0 --soft-reboot boardled off
python tools/led_serial_control.py --port /dev/ttyUSB0 --off
```

### 4. Demo de flash integrado

```bash
./scripts/flash_experiment.sh
```

Esto ejecuta `tools/run_led_flash_experiment.py` con webcam en indice `2`, modo raw, exposicion manual `10`, metrica `max`, `threshold-delta=30`, `5` pulsos de `300 ms`, `duty=1023`, preview y guardado de frames detectados.

### 5. Barrido de intensidad

```bash
./scripts/intensity_sweep.sh
```

Esto prueba duties `8,16,24,32,48,64,96,128,192,256,384,512,768,1023` con `3` pulsos por duty y guarda un CSV resumen. Para repetir el barrido bajo mas reciente, usar el comando exacto de `data/webcam/flash_experiment_results_20260521_additional.md` con duties `1,2,4,6,8,10,12,16,24,32`.

### 6. Barrido de parametros

```bash
./scripts/flash_parameter_sweep.sh
```

Esto varia exposicion y duracion de pulso. El script actual usa `duty=128`; los resultados bajos mas recientes usaron `duty=6`, `exposure=10`, duraciones `5,10,20,30,40,50,75,100,200` y estan documentados en `data/webcam/flash_experiment_results_20260521_additional.md`.

## Terminos clave

| Termino | Significado practico |
|---------|----------------------|
| `duty` | Intensidad PWM enviada al LED, escala `0-1023`. `0` apaga; `1023` es 100% de duty PWM. |
| Porcentaje de intensidad | `intensity_percent = duty / 1023 * 100`. Ejemplo: `duty=6` equivale a `0.59%`; `duty=512` equivale a `50.05%`. |
| Exposicion/integracion | Tiempo efectivo de acumulacion de luz por frame de la webcam. En este flujo se controla con `--auto-exposure manual --exposure <valor> --exposure-auto-priority 0`. |
| `threshold-delta` | Margen absoluto sumado al baseline oscuro. Si la metrica del frame supera `baseline + threshold_delta`, se marca flash. |
| `max` | Pixel mas brillante del frame o ROI. Es util cuando el LED ocupa pocos pixeles. |
| `p99` | Percentil 99 de intensidad. Mas estable para regiones grandes, pero puede ignorar flashes puntuales. |
| `mean` | Promedio de intensidad. Puede diluir un flash pequeno en todo el frame. |

## Resultados mas recientes

Configuracion comun: Logitech C525 en indice `2`, `640x480`, `YUYV`, `--raw`, exposicion manual, `--exposure-auto-priority 0`, metrica `max`, `threshold-delta=30`.

| Resultado | Valor | Evidencia |
|-----------|-------|-----------|
| FPS medido C525 | Aproximadamente `29.88 FPS` en `640x480 YUYV raw`. | `data/webcam/flash_experiment_results_20260521.md`, CSV `data/webcam/webcam_flash_metrics_20260521_114151.csv`. |
| Flujo integrado | `5/5` eventos detectados, `46` frames detectados. | `data/webcam/flash_experiment_results_20260521.md`. |
| Minimo detectable probado | `duty=6/1023 = 0.59%`, `3/3` eventos. | `data/webcam/flash_experiment_results_20260521_additional.md`, `data/webcam/led_intensity_low_sweep_20260521.csv`. |
| Duties no detectados | `duty=1`, `2`, `4` no detectados con `threshold-delta=30`. | `data/webcam/led_intensity_low_sweep_20260521.csv`. |
| Estabilidad demo | `duty=512` (`50.05%`), `200 ms`, detecto `10/10` eventos. | `data/webcam/webcam_flash_metrics_20260521_115855.csv`. |
| Duracion baja confiable | Con `duty=6`, `exposure=10`, `200 ms` fue confiable (`3/3`). | `data/webcam/flash_parameter_low_duty_20260521.csv`. |
| Duraciones bajas inestables | `5/10/20 ms` no fueron estables; `50 ms` tuvo deteccion parcial en barridos. | `data/webcam/flash_experiment_results_20260521.md` y `data/webcam/flash_experiment_results_20260521_additional.md`. |
| Robustez de umbral | Para `duty=6`, `threshold-delta=20` y `30` detectaron; `40` fue demasiado estricto. | `data/webcam/threshold_delta_20_duty6_20260521.csv`, `data/webcam/threshold_delta_40_duty6_20260521.csv`. |

Lectura importante: a ~30 FPS, pulsos muy cortos pueden caer entre frames o aportar poca energia integrada. Por eso `200 ms` fue confiable para `duty=6`, mientras duraciones menores quedaron parciales o no detectadas en esta configuracion.

## Evidencia visual

Los PNG de frames detectados estan en:

```text
data/webcam/flash_presentation/*
```

Subdirectorios utiles:

| Ruta | Uso recomendado |
|------|-----------------|
| `data/webcam/flash_presentation/demo_stability/` | Imagenes representativas de la demo estable. |
| `data/webcam/flash_presentation/demo_stability/` | Evidencia para mostrar estabilidad `10/10`. |
| `data/webcam/flash_presentation/intensity_low/` | Comparacion visual por intensidad baja. |
| `data/webcam/flash_presentation/low_duty_parameters/` | Evidencia de exposicion/duracion con `duty=6`. |
| `data/webcam/flash_presentation/threshold_delta_20/` | Evidencia de umbral menos estricto. |

Estas imagenes sirven para presentacion porque muestran frames reales que cruzaron el umbral. No reemplazan el CSV; complementan la evidencia numerica.

## Que no afirmar

| No afirmar | Afirmacion correcta |
|------------|---------------------|
| Que se uso una camara de alta velocidad. | Se uso una webcam Logitech C525 comun, medida cerca de `30 FPS`. |
| Que se detecto sonoluminiscencia real. | Se detectaron flashes de un LED externo como analogo controlado. |
| Que el sistema mide eventos ultrarrapidos aislados con precision temporal alta. | El sistema detecta estadisticamente flashes repetidos bajo limitaciones de FPS, exposicion y umbral. |
| Que cualquier GPIO onboard fue probado/controlado. | Solo se controla el LED onboard conocido en `GPIO2`; no se hizo escaneo arbitrario de GPIOs. |

## Checklist para el amigo/agente

- [ ] Confirmar que la webcam correcta aparece como indice OpenCV `2`.
- [ ] Confirmar que la ESP32 esta en `/dev/ttyUSB0`.
- [ ] Confirmar que el LED externo esta en `GPIO17` con resistencia limitadora.
- [ ] Confirmar que el LED rojo de power esta tapado fisicamente.
- [ ] Ejecutar `./scripts/esp32_all_off.sh` antes de cualquier medicion.
- [ ] Tratar `./scripts/flash_experiment.sh` como ruta **demo** no productiva (`run_intent=demo`).
- [ ] Tratar `./scripts/intensity_sweep.sh` como ruta **tuning** no productiva (`run_intent=tuning`).
- [ ] Antes de producción new-mount, preparar una corrida `dark-control` y verificar freshness <= 5 minutos.
- [ ] Definir `campaign_id` y mantener `mount_context=new-camera-mount` en todo el lote.
- [ ] Verificar que el lote productivo tenga 10 corridas independientes (`run_index` 1..10), 120 s c/u e intervalos 1.8–2.2 s.
- [ ] Usar `scripts/new_mount_campaign_batch.sh <campaign-id> <dark-control-ref>` solo cuando la etapa operativa esté aprobada.
- [ ] En toda corrida con webcam o flujo dual, usar preview cuando sea factible para verificar visualmente que el LED ilumina de verdad.
- [ ] Si una corrida no puede usar preview por falta de display, seguridad o limitacion del entorno, dejar esa excepcion escrita en el reporte final con su motivo.
- [ ] Ejecutar `./scripts/flash_experiment.sh` y verificar que el CSV reporte eventos detectados.
- [ ] Revisar CSV en `data/webcam/` y PNG en `data/webcam/flash_presentation/`.
- [ ] No modificar hardware ni escanear GPIOs salvo que el usuario lo pida explicitamente.

## Proximo trabajo recomendado

| Prioridad | Trabajo | Motivo |
|-----------|---------|--------|
| Alta | Tren de pulsos con intervalo aleatorio `1.8-2.1 s`. | Evita que la deteccion parezca sincronizada o dependiente de un periodo fijo. |
| Alta | Captura larga de `5-10 min`. | Genera estadistica mas fuerte de falsos positivos, falsos negativos y estabilidad. |
| Media | Reconstruccion visual desde multiples coincidencias. | Permite mostrar detecciones acumuladas y patrones de presencia de flash. |
| Media | Firmware Arduino/C++ o ESP-IDF si hace falta microsegundos. | MicroPython es suficiente para esta demo, pero no ideal si se necesita generacion de pulsos a nivel microsegundo. |

## Referencias internas

| Archivo | Contenido |
|---------|-----------|
| `docs/webcam_led_flash_experiment.md` | Guia operativa principal del experimento. |
| `data/webcam/flash_experiment_results_20260521.md` | Resultados base: FPS, demo integrada, barrido inicial de intensidad y parametros. |
| `data/webcam/flash_experiment_results_20260521_additional.md` | Resultados adicionales: duty bajo, estabilidad, exposicion/duracion, robustez de umbral. |
| `tools/webcam_flash_detector.py` | Detector por frame y generador de CSV/PNG. |
| `hardware/led_pulse_controller.py` | Firmware MicroPython para controlar el LED externo. |
| `scripts/*.sh` | Entradas rapidas para apagar, demo y barridos. |
