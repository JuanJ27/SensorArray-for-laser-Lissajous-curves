# Resultados adicionales del experimento webcam + LED - 2026-05-21

## Montaje usado

- Se mantuvo el montaje existente: ESP32 con LED experimental en `GPIO 17`, Logitech C525 en caja oscura, indice OpenCV `2`.
- No se hicieron modificaciones fisicas ni se escanearon GPIOs arbitrarios.
- El LED onboard controlable se mantuvo apagado con `boardled off`, que escribe `GPIO 2 = 0`.
- El LED rojo de power esta cubierto fisicamente por el usuario.
- Configuracion comun de camara: `640x480`, `YUYV`, `--raw`, metrica `max`, exposicion manual, `--exposure-auto-priority 0`.

## Terminologia

`duty` es la intensidad PWM enviada al LED en escala `0-1023`. El porcentaje equivalente se calcula con:

```text
intensity_percent = duty / 1023 * 100
```

| Duty | Intensidad |
|------|------------|
| 1 | 0.10% |
| 2 | 0.20% |
| 4 | 0.39% |
| 6 | 0.59% |
| 8 | 0.78% |
| 10 | 0.98% |
| 12 | 1.17% |
| 16 | 1.56% |
| 24 | 2.35% |
| 32 | 3.13% |
| 128 | 12.51% |
| 512 | 50.05% |
| 1023 | 100.00% |

## Comandos usados

### A. Estabilidad del demo

```bash
.venv/bin/python tools/run_led_flash_experiment.py --port /dev/ttyUSB0 --index 2 --raw --auto-exposure manual --exposure 10 --exposure-auto-priority 0 --metric max --threshold-delta 30 --count 10 --period-ms 700 --duration-ms 200 --duty 512 --seconds 12 --warmup 0.5 --calibration 2 --preview --save-detected-frames --frames-dir data/webcam/flash_presentation/demo_stability
```

Resultado: `10` eventos detectados de `10` pulsos esperados, `60` frames detectados, `29.87 FPS`.

CSV: `data/webcam/webcam_flash_metrics_20260521_115855.csv`

Imagenes: `data/webcam/flash_presentation/demo_stability/`

### B. Caracterizacion de intensidad baja

```bash
.venv/bin/python tools/run_led_intensity_sweep.py --port /dev/ttyUSB0 --index 2 --raw --auto-exposure manual --exposure 10 --exposure-auto-priority 0 --metric max --threshold-delta 30 --duties 1,2,4,6,8,10,12,16,24,32 --count 3 --period-ms 700 --duration-ms 200 --seconds 7 --warmup 0.5 --calibration 2 --preview --save-detected-frames --frames-dir data/webcam/flash_presentation/intensity_low --output data/webcam/led_intensity_low_sweep_20260521.csv
```

CSV resumen: `data/webcam/led_intensity_low_sweep_20260521.csv`

Imagenes: `data/webcam/flash_presentation/intensity_low/`

| Duty | Intensidad | Eventos detectados | Frames detectados | CSV por corrida |
|------|------------|--------------------|-------------------|-----------------|
| 1 | 0.10% | 0 | 0 | `data/webcam/webcam_flash_metrics_20260521_115919.csv` |
| 2 | 0.20% | 0 | 0 | `data/webcam/webcam_flash_metrics_20260521_115929.csv` |
| 4 | 0.39% | 0 | 0 | `data/webcam/webcam_flash_metrics_20260521_115940.csv` |
| 6 | 0.59% | 3 | 14 | `data/webcam/webcam_flash_metrics_20260521_115950.csv` |
| 8 | 0.78% | 3 | 18 | `data/webcam/webcam_flash_metrics_20260521_120001.csv` |
| 10 | 0.98% | 3 | 18 | `data/webcam/webcam_flash_metrics_20260521_120011.csv` |
| 12 | 1.17% | 3 | 18 | `data/webcam/webcam_flash_metrics_20260521_120022.csv` |
| 16 | 1.56% | 3 | 18 | `data/webcam/webcam_flash_metrics_20260521_120032.csv` |
| 24 | 2.35% | 3 | 18 | `data/webcam/webcam_flash_metrics_20260521_120043.csv` |
| 32 | 3.13% | 3 | 18 | `data/webcam/webcam_flash_metrics_20260521_120053.csv` |

Minimo detectable probado: `duty=6`, equivalente a `0.59%`, con `3/3` eventos detectados. `duty=1`, `2` y `4` no fueron detectados con estos parametros.

### C. Caracterizacion de exposicion/integracion

```bash
.venv/bin/python tools/run_flash_parameter_sweep.py --port /dev/ttyUSB0 --index 2 --raw --metric max --threshold-delta 30 --duty 6 --count 3 --period-ms 700 --duration-ms 200 --exposure 10 --exposures 3,5,10,20,40 --durations-ms 5,10,20,30,40,50,75,100,200 --seconds 7 --warmup 0.5 --calibration 2 --preview --save-detected-frames --frames-dir data/webcam/flash_presentation/low_duty_parameters --output data/webcam/flash_parameter_low_duty_20260521.csv
```

CSV resumen: `data/webcam/flash_parameter_low_duty_20260521.csv`

Imagenes: `data/webcam/flash_presentation/low_duty_parameters/`

| Exposicion | Duty | Intensidad | Duracion | Eventos detectados | Frames detectados |
|------------|------|------------|----------|--------------------|-------------------|
| 3 | 6 | 0.59% | 200 ms | 3 | 3 |
| 5 | 6 | 0.59% | 200 ms | 6 | 7 |
| 10 | 6 | 0.59% | 200 ms | 4 | 5 |
| 20 | 6 | 0.59% | 200 ms | 3 | 18 |
| 40 | 6 | 0.59% | 200 ms | 3 | 18 |

Lectura: con intensidad muy baja (`duty=6`), la webcam detecta flashes en todo el rango de exposiciones probado, pero las exposiciones `5` y `10` generaron eventos extra. Para una demostracion mas limpia de conteo exacto, `exposure=3`, `20` o `40` dieron `3/3` eventos en esta ronda.

### D. Caracterizacion de duracion de pulso

Misma corrida que la seccion anterior, con `duty=6`, `exposure=10` y `threshold-delta=30`.

| Duracion | Duty | Intensidad | Eventos detectados | Frames detectados |
|----------|------|------------|--------------------|-------------------|
| 5 ms | 6 | 0.59% | 0 | 0 |
| 10 ms | 6 | 0.59% | 0 | 0 |
| 20 ms | 6 | 0.59% | 0 | 0 |
| 30 ms | 6 | 0.59% | 1 | 1 |
| 40 ms | 6 | 0.59% | 0 | 0 |
| 50 ms | 6 | 0.59% | 1 | 1 |
| 75 ms | 6 | 0.59% | 2 | 3 |
| 100 ms | 6 | 0.59% | 0 | 0 |
| 200 ms | 6 | 0.59% | 3 | 3 |

Lectura: para este montaje y una intensidad muy baja, el umbral practico confiable esta en `200 ms`. Entre `30` y `100 ms` hay detecciones parciales/no estables, probablemente por la relacion entre el pulso, el frame rate de ~30 FPS y el umbral.

### E. Robustez de umbral

Comandos:

```bash
.venv/bin/python tools/run_led_intensity_sweep.py --port /dev/ttyUSB0 --index 2 --raw --auto-exposure manual --exposure 10 --exposure-auto-priority 0 --metric max --threshold-delta 20 --duties 6 --count 3 --period-ms 700 --duration-ms 200 --seconds 7 --warmup 0.5 --calibration 2 --preview --save-detected-frames --frames-dir data/webcam/flash_presentation/threshold_delta_20 --output data/webcam/threshold_delta_20_duty6_20260521.csv
.venv/bin/python tools/run_led_intensity_sweep.py --port /dev/ttyUSB0 --index 2 --raw --auto-exposure manual --exposure 10 --exposure-auto-priority 0 --metric max --threshold-delta 40 --duties 6 --count 3 --period-ms 700 --duration-ms 200 --seconds 7 --warmup 0.5 --calibration 2 --preview --save-detected-frames --frames-dir data/webcam/flash_presentation/threshold_delta_40 --output data/webcam/threshold_delta_40_duty6_20260521.csv
```

| Threshold delta | Duty | Intensidad | Eventos detectados | Frames detectados | CSV |
|-----------------|------|------------|--------------------|-------------------|-----|
| 20 | 6 | 0.59% | 3 | 18 | `data/webcam/threshold_delta_20_duty6_20260521.csv` |
| 30 | 6 | 0.59% | 3 | 14 | `data/webcam/led_intensity_low_sweep_20260521.csv` |
| 40 | 6 | 0.59% | 0 | 0 | `data/webcam/threshold_delta_40_duty6_20260521.csv` |

Lectura: `threshold-delta=30` funciona como punto medio practico para detectar `duty=6`; `40` es demasiado estricto para esa intensidad baja.

## Conclusiones para los requisitos del profesor

- Cambio de intensidad LED: queda demostrado con el barrido de `duty=1..32`, reportado tambien en porcentaje.
- Cambio de integracion/exposicion: queda demostrado con el barrido `exposure=3,5,10,20,40`; la cantidad de frames y eventos detectados cambia con la exposicion.
- Deteccion de flash: el detector registra CSV por frame, cuenta eventos y guarda imagenes PNG de frames detectados.
- Evidencia visual: las imagenes para presentacion estan bajo `data/webcam/flash_presentation/`.
- Estabilidad: con `duty=512` (`50.05%`) y pulsos de `200 ms`, la demo detecto `10/10` eventos.

## Advertencia tecnica

Este montaje con LED es un analogo controlado de detectabilidad de destellos. Sirve para evaluar camara, exposicion/integracion, umbral e intensidad, pero no es sonoluminiscencia real.
