# 📊 Dataset Documentation

## Descripción General

Esta carpeta contiene los datasets experimentales capturados por el sistema de arreglo de sensores. Todos los archivos están en formato CSV y siguen la estructura estándar documentada en [`docs/data_format.md`](../docs/data_format.md).

## Salidas derivadas offline

Además de los datos crudos e intermedios, el repositorio ahora usa estas carpetas derivadas reproducibles:

- `data/derived/catalog/`: catálogo y validación de corridas.
- `data/derived/normalized/`: normalización conservadora de artefactos heredados.
- `data/derived/studies/`: agregaciones por estudio, condición y corrida.
- `data/derived/presentation/`: resúmenes Markdown en español y plots para presentación si el entorno puede renderizarlos.

Regeneración recomendada:

```bash
python3 scripts/build_run_catalog.py
python3 scripts/normalize_legacy_runs.py
python3 scripts/build_study_summaries.py
```

## Archivos Disponibles

### 📈 Patrones de Movimiento Controlado

| Archivo | Descripción | Patrón | Duración | Frecuencia |
|---------|-------------|---------|----------|------------|
| `horizontal_sweep.csv` | Barrido horizontal | Izq ↔ Der | ~30s | 0.5-2 Hz |
| `vertical_sweep.csv` | Barrido vertical | Abajo ↕ Arriba | ~30s | 0.5-2 Hz |
| `diagonal_pattern.csv` | Movimiento diagonal | Esquina a esquina | ~45s | Variable |

### 🎲 Patrones Aleatorios y Pruebas

| Archivo | Descripción | Propósito | Características |
|---------|-------------|-----------|-----------------|
| `random_motion_1.csv` | Movimiento aleatorio #1 | Calibración/Testing | Sin patrón específico |
| `random_motion_2.csv` | Movimiento aleatorio #2 | Validación algoritmos | Movimiento errático |
| `experimental_test.csv` | Prueba experimental | Validación sistema | Condiciones controladas |

### 📍 Datos de Referencia

| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `position_reference.csv` | Posiciones de referencia | Calibración espacial |

## Formato de Datos

Todos los archivos CSV siguen esta estructura:
```csv
tiempo,azul,verde,amarillo,naranja,rojo
0,1024,2048,3072,1536,2560
10,1034,2038,3062,1546,2550
```

### Columnas
- **tiempo**: Timestamp en milisegundos desde inicio de captura
- **azul**: Sensor azul en (0.2, 0.0) - Valores ADC 0-4095
- **verde**: Sensor verde en (0.0, 1.0) - Valores ADC 0-4095  
- **amarillo**: Sensor amarillo en (0.47, 0.6) - Valores ADC 0-4095
- **naranja**: Sensor naranja en (0.8, 0.0) - Valores ADC 0-4095
- **rojo**: Sensor rojo en (1.0, 1.0) - Valores ADC 0-4095

## Disposición Espacial de Sensores

```
Verde (0,1) 🟢      🔴 Rojo (1,1)
              
         🟡 Amarillo (0.47,0.6)
              
Azul (0.2,0) 🔵     🟠 Naranja (0.8,0)
```

## Características Técnicas

### Parámetros de Captura
- **Frecuencia de muestreo**: 10 Hz (100ms entre muestras)
- **Resolución ADC**: 12-bit (0-4095)
- **Rango de voltaje**: 0-3.3V
- **Atenuación**: 11dB para rango completo

### Calidad de Datos
- **Valores típicos en oscuridad**: 50-100 ADC
- **Valores típicos con iluminación**: 200-3500 ADC  
- **Saturación**: >3800 ADC
- **Ruido estimado**: ±20 ADC en condiciones normales

## Uso Recomendado

### Para Análisis Básico
```python
import pandas as pd

# Cargar datos
df = pd.read_csv('data/horizontal_sweep.csv')

# Información básica
print(f"Duración: {(df['tiempo'].max() - df['tiempo'].min()) / 1000:.1f} segundos")
print(f"Muestras: {len(df)}")
print(f"Frecuencia promedio: {len(df) / ((df['tiempo'].max() - df['tiempo'].min()) / 1000):.1f} Hz")
```

### Para Análisis Avanzado
Ver el notebook [`notebooks/analisis_fototransistores.ipynb`](../notebooks/analisis_fototransistores.ipynb) para ejemplos completos de:
- Reconstrucción de trayectorias
- Análisis frecuencial
- Detección de patrones
- Visualización de datos

## Metadatos de Captura

### Condiciones Experimentales
- **Fecha de captura**: Marzo 2024
- **Hardware**: ESP32 + 5x OP598
- **Láser**: 635nm, potencia ajustable
- **Ambiente**: Laboratorio con iluminación controlada
- **Temperatura**: ~20-25°C

### Configuración del Circuito
- **Resistencias pull-down**: 100kΩ
- **Alimentación**: 3.3V desde ESP32
- **Conexiones**: Ver [`docs/hardware_setup.md`](../docs/hardware_setup.md)

## Contribuciones

Para añadir nuevos datasets:

1. **Seguir convención de nombres**: `tipo_movimiento_version.csv`
2. **Documentar metadatos**: Condiciones de captura, configuración, etc.
3. **Validar formato**: Usar estructura CSV estándar
4. **Añadir descripción**: Actualizar esta documentación

## Licencia

Los datos están disponibles bajo la misma licencia del proyecto (MIT). Se permite uso libre con atribución apropiada.

---

💡 **Tip**: Para análisis interactivo, usa el notebook Jupyter que incluye funciones preconfiguradas para cargar y analizar estos datasets.
