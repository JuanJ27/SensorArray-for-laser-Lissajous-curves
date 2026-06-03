# Datos preliminares para análisis de cámara web

Objetivo: preparar la segunda parte de resultados del artículo, correspondiente al acondicionamiento optoelectrónico y la detectabilidad visual con cámara web.

## Archivos clave

### Ruido basal de cámara
- `datos_crudos/dark_control_webcam_only_reassembled_20260526.csv`
- Columnas importantes: `mean`, `max`, `p99`, `threshold`, `detected`.
- Usar `max` como brillo máximo por fotograma y `mean` como brillo medio por fotograma.
- El umbral de detección sugerido para el análisis es: media(`max`) + 3 * desviación estándar(`max`).

### Barrido de intensidad del LED
- Agregado: `datos_derivados/webcam_intensity_by_duty.csv`
- Observaciones por corrida: `datos_derivados/webcam_intensity_observations.csv`
- CSVs crudos de barridos: `datos_crudos/led_intensity_sweep_20260526_184256.csv`, `datos_crudos/led_intensity_sweep_20260526_185645.csv`, `datos_crudos/led_intensity_sweep_20260526_191013.csv`
- Variables principales: `duty`, `expected_pulses`, `detection_events`, `bounded_detected_pulses`, `detection_probability`, `metrics_csv`.

### Barrido de duración y exposición
- Duración agregada: `datos_derivados/webcam_parameter_by_duration.csv`
- Exposición agregada: `datos_derivados/webcam_parameter_by_exposure.csv`
- Observaciones por corrida: `datos_derivados/webcam_parameter_observations.csv`
- CSVs crudos de barridos: `datos_crudos/flash_parameter_sweep_20260521_114453.csv`, `datos_crudos/flash_parameter_low_duty_20260521.csv`
- Variables principales: `duty`, `duration_ms`, `exposure`, `expected_pulses`, `detection_events`, `bounded_detected_pulses`, `detection_probability`, `metrics_csv`.

## Advertencias para la redacción

- La cámara web no mide la forma temporal real del pulso; solo detecta energía integrada por fotograma.
- La probabilidad de detección ya está acotada con `bounded_detected_pulses`, para evitar sobrecontar eventos cuando un mismo pulso se segmenta en más de una detección.
- Los barridos de duración y exposición tienen pocas réplicas; reportar como resultados condicionados por esta configuración experimental, no como umbrales universales.
- Los datos de intensidad de 2026-05-26 incluyen duties bajos con 60 pulsos esperados por corrida, útiles para estimar detectabilidad práctica.

## Prompt sugerido para otra IA

Contexto:
Estoy escribiendo un artículo científico sobre la detectabilidad visual de destellos LED con una cámara web comercial. Necesito procesar estos CSV para generar estadísticas y gráficas de la sección de resultados.

Tareas:
1. A partir de `dark_control_webcam_only_reassembled_20260526.csv`, calcula media y desviación estándar de `max` y `mean`. Define un umbral estricto como media(`max`) + 3 * desviación estándar(`max`).
2. Con `webcam_intensity_by_duty.csv` y `webcam_intensity_observations.csv`, resume la detectabilidad frente al ciclo de trabajo del LED. Usa `bounded_detected_pulses / expected_pulses` o `detection_probability`.
3. Con `webcam_parameter_by_duration.csv`, `webcam_parameter_by_exposure.csv` y `webcam_parameter_observations.csv`, resume detectabilidad frente a duración y exposición.
4. Genera figuras académicas: histograma de ruido basal y umbral, detectabilidad frente a duty/duración, y efecto de exposición si los datos lo permiten.
5. Entrega tablas Markdown y figuras en PDF/PNG.
