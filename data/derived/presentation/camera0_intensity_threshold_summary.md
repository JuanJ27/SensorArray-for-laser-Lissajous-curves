# Resumen de umbral de intensidad - cámara 0

> Plantilla operativa para handoff y aceptación de campaña `camera0-intensity-threshold-statistics`.
> Esta plantilla NO ejecuta adquisición; define gates y evidencias requeridas.

## Contexto de campaña

- ID de campaña: `camera0-intensity-threshold-statistics`
- Intención de corrida obligatoria: `run_intent=threshold`
- Cámara obligatoria: `camera_index=0`
- Política: sin pooling legado entre campañas ni entre cámaras.

## Checklist de aceptación

Marcá cada punto al cerrar una corrida de análisis:

- [ ] **Identidad**: `campaign_id` presente y consistente en todos los artefactos.
- [ ] **Filtro cámara**: cohorte validada con `camera_index=0`.
- [ ] **Gates operatorios**: corrida live documentada con preview + preflight + confirmación de operador.
- [ ] **Contrato de artefactos**: todos los archivos requeridos existen.
- [ ] **Controles y cobertura**: reporte confirma duties requeridos y controles (dark + positivos).
- [ ] **Trazabilidad**: fecha, autor y comando usados registrados en notas de campaña.

## Artefactos obligatorios (deben existir)

### Tablas de estudio

- [ ] `data/derived/studies/camera0_intensity_per_pulse.csv`
- [ ] `data/derived/studies/camera0_intensity_by_duty_wilson.csv`
- [ ] `data/derived/studies/camera0_threshold_estimates.csv`
- [ ] `data/derived/studies/camera0_validation_report.csv`

### Gráficos de presentación

- [ ] `data/derived/presentation/plots/camera0_duty_detection_ci.png`
- [ ] `data/derived/presentation/plots/camera0_threshold_bootstrap.png`

## Registro de aceptación

- Responsable:
- Fecha:
- Estado final: ✅ Aceptado / ⚠️ Incompleto / ❌ Rechazado
- Observaciones:
