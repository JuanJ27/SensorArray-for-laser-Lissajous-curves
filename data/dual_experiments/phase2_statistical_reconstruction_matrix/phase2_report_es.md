# Reporte fase dual estadistica

## Idea

Esta fase usa reconstruccion estadistica por flashes repetidos.
No intenta capturar un flash ultracorto en un unico frame perfecto.

- OP598 en `ADC36` = ancla temporal optica aproximada.
- Webcam C525 a `~30 FPS` = canal visual de coincidencia.
- Intervalos aleatorios `1800-2100 ms` = evitan lock simple con la camara.

## Configuracion comun de webcam

- `index=2`
- `640x480`
- `YUYV --raw`
- `auto-exposure manual`
- `exposure=20`
- `exposure-auto-priority=0`
- `metric=max`
- `threshold-delta=4`
- `sigma-multiplier=1.0`
- `coincidence-window-ms=100`

## Corridas ejecutadas

### A. Smoke random

- Run: `random-train_20260522_155311`
- Comando base: `count=10`, `duration_ms=40`, `duty=32`
- OP598 pulse events: `10/10`
- Pulsos con deteccion webcam en ventana: `5/10`
- Artefactos: `manifest.json`, `pulse_events.csv`, `coincidence_table.csv`, `webcam_capture.avi`, `visuals/`

### B. Baja intensidad

- Run: `random-train_20260522_155351`
- Comando base: `count=10`, `duration_ms=40`, `duty=8`
- OP598 pulse events: `10/10`
- Pulsos con deteccion webcam en ventana: `6/10`
- Lectura cauta: hubo coincidencia recuperable, pero con ruido apreciable y falsos positivos fuera de ventana.

### C. Pulso corto

- Run: `random-train_20260522_155431`
- Comando base: `count=10`, `duration_ms=20`, `duty=32`
- OP598 pulse events: `10/10`
- Pulsos con deteccion webcam en ventana: `0/10`
- Conclusion: en esta configuracion el pulso corto queda por debajo de detectabilidad visual practica.

## Que significan los artefactos

- `pulse_events.csv`: tabla por pulso usando el OP598 como ancla temporal gruesa.
- `coincidence_table.csv`: join por pulso hacia el frame webcam mas cercano y detecciones dentro de ventana.
- `webcam_capture.avi`: video completo del run para relectura posterior.
- `visuals/average_frame.png`: promedio de frames emparejados por pulso.
- `visuals/coincidence_heatmap.png`: mapa de energia visual acumulada.
- `visuals/pulse_strip.png`: tira before/during/after de frames emparejados.
- `dual_summary.md`: lectura humana en castellano por corrida.

## Limites actuales

- El OP598 NO esta entregando timing fino: la cadencia real observada sigue alrededor de `6.4-6.6 ms`.
- La webcam recupera coincidencia estadistica, no timing optico rapido.
- Con `exposure=20` y umbral bajo se recuperan coincidencias, pero aumenta ruido visual fuera de ventana.
- Para demo, las corridas mas utiles hoy son `40 ms @ duty 32` y `40 ms @ duty 8` con filtro por ventana OP598.
