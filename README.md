# 🔬 SensorArray for Laser Lissajous Curves

Un proyecto de investigación universitaria que implementa un sistema de detección y análisis de curvas de Lissajous usando un arreglo de sensores. El sistema utiliza MicroPython en ESP32 y 5 fototransistores para capturar y analizar patrones de movimiento de láser.
**IMPORTANTE:** Aun no se realiza el analisis en las curvas de lisajous, por ahora la informacion medida son de una luz roja movida a mano.

![Project Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8+-yellow)

## Características

- **Arreglo de 5 fototransistores** OP598 NPNs dispuestos estratégicamente
- **Microcontrolador ESP32** con MicroPython para control y adquisición de datos
- **Análisis en tiempo real** de patrones de movimiento láser
- **Detección de curvas de Lissajous** y patrones geométricos
- **Visualización interactiva** de datos y análisis estadístico

## Configuración del Hardware

### Componentes
- 1x ESP32 (MicroPython v1.22.2)
- 5x Fototransistores OP598 NPN
- 5x Resistencias de 100kΩ
- 1x LED de 635nm
- Protoboard y cables de conexión

### Disposición Espacial de Sensores

![Diagrama de la disposición espacial de sensores](assets/diagrama.png)

### Conexiones Eléctricas
- **Alimentación**: 3.3V compartido (ESP32)
- **Tierra**: Común con ESP32
- **Señales analógicas**: Pines ADC del ESP32
  - Azul: Pin 39
  - Verde: Pin 36  
  - Amarillo: Pin 34
  - Naranja: Pin 35
  - Rojo: Pin 4

## 🚀 Inicio Rápido

### Requisitos del Sistema
```bash
# Dependencias de Python
numpy>=1.21.0
pandas>=1.3.0
matplotlib>=3.4.0
scipy>=1.7.0
jupyter>=1.0.0
```

### Instalación
1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/JuanJ27/SensorArray-for-laser-Lissajous-curves.git
   cd SensorArray-for-laser-Lissajous-curves
   ```

2. **Configurar el entorno Python**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Flashear MicroPython en ESP32**
   ```bash
   # Usar el firmware incluido en hardware/firmware/
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 hardware/firmware/ESP32_GENERIC-20240222-v1.22.2.bin
   ```

4. **Cargar código del sensor**
   ```bash
   # Copiar sensor_array.py al ESP32 como main.py
   ampy --port /dev/ttyUSB0 put hardware/sensor_array.py main.py
   ```

5. **Cargar prueba de latencia**
   ```bash
   # Copiar latency_test.py al ESP32 para medir latencia practica
   ampy --port /dev/ttyUSB0 put hardware/latency_test.py latency_test.py
   ```

### Uso Básico
1. **Ejecutar captura de datos**
   - `sensor_array.py` realiza muestreo periodico de los 5 sensores
   - El ESP32 emite las muestras CSV por puerto serie
   - La PC guarda los archivos con fecha y hora en `data/captures/`
   ```bash
   python3 tools/capture_sensor_data.py --port /dev/ttyUSB0
   ```

2. **Ejecutar caracterizacion temporal**
    - `latency_test.py` mide la latencia practica del sistema con un LED en `GPIO 17`
    - El sensor objetivo por defecto es el verde en `GPIO 36`
    - La medicion usa ADC con umbral calibrado y polling intensivo
    - El resultado representa latencia de deteccion en MicroPython, no la respuesta intrinseca aislada del OP598

3. **Ejecutar flujo dual OP598 + webcam**
    - `hardware/led_pulse_controller.py` ahora controla el LED en `GPIO 17` y captura el OP598 montado en `verde`, `ADC36`
    - `tools/capture_op598_response.py` guarda CSV, resumen y plots del canal numerico
    - `tools/run_dual_flash_experiment.py` coordina canal numerico + webcam C525 en indice `2`
    - Este flujo estima detectabilidad y tiempos practicos del sistema `LED + circuito + OP598 + ESP32`, no metrologia ultrarrapida de laboratorio

3. **Análisis de datos**
   ```bash
   jupyter notebook notebooks/analisis_fototransistores.ipynb
   ```

### Webcam USB con OpenCV

Usa `tools/webcam_fps_tool.py` para probar una webcam USB sin mezclarla con las
herramientas del ESP32. En Linux el script prefiere `CAP_V4L2` y pide `MJPG`,
que suele entregar mejor FPS real que formatos sin compresión.

Para el flujo minimo webcam + LED con deteccion de destellos, seguí la guía
práctica en [`docs/webcam_led_flash_experiment.md`](docs/webcam_led_flash_experiment.md).
Incluye cableado seguro, carga del firmware MicroPython, control PWM del LED y
comandos exactos para medir destellos con la Logitech C525.

Para el flujo dual con el OP598 conectado al canal `verde` en `ADC36`, usá la
nueva sección de la misma guía. Ese canal numérico es bastante más útil que la
webcam para separar pulsos cortos, pero sigue estando limitado por el ADC y el
overhead de MicroPython.

Camino rápido para la Logitech HD Webcam C525:

```bash
source .venv/bin/activate
python tools/webcam_fps_tool.py probe --list
python tools/webcam_fps_tool.py probe --index 0 --width 640 --height 480 --fps 30 --fourcc MJPG --seconds 5
python tools/webcam_fps_tool.py record --index 0 --width 640 --height 480 --fps 30 --fourcc MJPG --seconds 5
```

Agregá `--preview` si querés ver la imagen mientras se mide o graba:

```bash
python tools/webcam_fps_tool.py probe --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --seconds 10 --preview
```

Para medir el throughput real de la cámara sin pagar el costo de convertir cada
frame a BGR dentro de OpenCV, usá `--raw`. En la C525 esto suele ser la prueba
más honesta para saber si el USB/cámara está entregando 30 FPS:

```bash
python tools/webcam_fps_tool.py probe --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --seconds 5 --raw
```

Para comparar modos:

```bash
python tools/webcam_fps_tool.py probe --index 0 --width 320,640,1280 --height 240,480,720 --fps 30 --fourcc MJPG,YUYV --seconds 3
```

Si el FPS medido queda muy bajo, probá desactivar la exposición automática. En
webcams UVC como la C525, poca luz puede hacer que la cámara alargue la
exposición y entregue menos cuadros por segundo:

```bash
python tools/webcam_fps_tool.py probe --index 2 --width 640 --height 480 --fps 30 --fourcc YUYV --seconds 5 --raw --auto-exposure manual --exposure 10 --exposure-auto-priority 0
```

Notas prácticas:

- Si `/dev/video0` no es la webcam correcta, cambiá `--index` por el índice que
  aparece en `probe --list`.
- El FPS pedido no garantiza el FPS real: mirá `actual_fps`, `actual_fourcc` y
  `measured_fps` en la salida.
- Si ya sabés el índice de la cámara, pasá `--index`; así el script no recorre
  otros nodos `/dev/video*` y evita warnings innecesarios.
- No fuerces `--buffer-size 1` cuando busques máximo FPS. En la C525 puede bajar
  la medición a ~15 FPS. Usalo solo si estás optimizando latencia y aceptás ese
  costo.
- La C525 normalmente está limitada a alrededor de 30 FPS; bajar resolución o
  usar `MJPG` puede mejorar la estabilidad, no superar límites físicos del modo.
- Los clips se guardan por defecto en `data/webcam/`.

## Estructura del Proyecto

```
📁 SensorArray-for-laser-Lissajous-curves/
├── 📄 README.md              # Este archivo
├── 📄 LICENSE                # Licencia del proyecto
├── 📄 requirements.txt       # Dependencias Python
├── 📁 tools/                 # Scripts de captura en PC
│   ├── 📄 capture_sensor_data.py
│   └── 📄 webcam_fps_tool.py
├── 📁 hardware/              # Código y firmware del hardware
│   ├── 📄 sensor_array.py    # Muestreo periódico de 5 sensores
│   ├── 📄 latency_test.py    # Medición de latencia con 1 sensor
│   └── 📁 firmware/          # Firmware ESP32
├── 📁 notebooks/             # Análisis y visualizaciones
│   └── 📄 analisis_fototransistores.ipynb
├── 📁 data/                  # Datasets experimentales
│   ├── 📄 horizontal_sweep.csv
│   ├── 📄 vertical_sweep.csv
│   ├── 📄 diagonal_pattern.csv
│   └── 📄 random_motion.csv
├── 📁 docs/                  # Documentación técnica
│   ├── 📄 hardware_setup.md
│   ├── 📄 data_format.md
│   └── 📄 analysis_guide.md
├── 📁 assets/                # Imágenes y recursos
│   ├── 📄 circuit_diagram.png
│   ├── 📄 sensor_layout.png
│   └── 📄 sample_plots.png
└── 📁 results/               # Resultados y presentaciones
    └── 📄 Analisis_Fototransistores.pptx
```

## 🔬 Metodología

### Tipos de Patrones Detectados
1. **Movimiento Horizontal** - Barrido lineal en eje X
2. **Movimiento Vertical** - Barrido lineal en eje Y  
3. **Patrones Diagonales** - Movimientos en 45°
4. **Movimiento Aleatorio** - Para calibración y pruebas

### Formato de Datos
Los datos se capturan en formato CSV con la siguiente estructura:
```csv
tiempo,azul,verde,amarillo,naranja,rojo
0,1024,2048,3072,1536,2560
```
- **Tiempo**: Timestamp en milisegundos
- **Sensores**: Valores ADC (0-4095, resolución 12-bit)
- **Ubicacion de guardado**: La PC crea archivos como `sensor_data_20260428_121530.csv`

### Medicion de Latencia
La prueba de latencia usa un LED externo conectado a `GPIO 17` y el sensor verde
en `GPIO 36`. El script calibra un umbral ADC a partir de un nivel oscuro y uno
iluminado, luego mide en microsegundos el tiempo entre encender el LED y
detectar el cruce de umbral.

Esta prueba sirve para caracterizar la latencia practica de la cadena completa
en ESP32 con MicroPython. No debe interpretarse como una medicion aislada de la
respuesta fisica del fototransistor.

## Canal OP598 en ADC36

El montaje actual agrega un uso específico del sensor `verde`:

- `GPIO 17`: LED externo experimental
- `GPIO 36`: salida analógica del OP598 conectado a `verde`
- `GPIO 2`: LED onboard mantenido en comportamiento seguro; el firmware solo usa `boardled off`
- Webcam Logitech C525: `OpenCV --index 2`

Comandos de firmware disponibles para este flujo:

```bash
python tools/led_serial_control.py --port /dev/ttyUSB0 sensor status
python tools/capture_op598_response.py --port /dev/ttyUSB0 sample --sample-count 200 --sample-delay 1 --sample-unit ms
python tools/capture_op598_response.py --port /dev/ttyUSB0 pulse --duration-ms 40 --duty 1023 --pre-ms 40 --post-ms 120 --sample-us 1000
python tools/run_dual_flash_experiment.py --port /dev/ttyUSB0 --index 2 --raw --auto-exposure manual --exposure 10 pulse --duration-ms 40 --duty 1023
```

Interpretación correcta:

- El canal OP598 mide la respuesta práctica del sistema óptico y electrónico, no la física intrínseca de eventos nanosegundo a nanosegundo.
- El `sample_us` del firmware es un pedido aproximado. En MicroPython, el tiempo real queda afectado por `adc.read()`, `print()` y el intérprete.
- La webcam sigue siendo un canal lento, útil para evidencia visual, ventanas estadísticas y coincidencia a nivel frame.

## Resultados

El sistema es capaz de:
-  Generar visualizaciones temporales
-  Exportar datos para análisis posterior

## Contribuciones

Las contribuciones son bienvenidas.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## Autor

**Juan J** - [JuanJ27](https://github.com/JuanJ27)
