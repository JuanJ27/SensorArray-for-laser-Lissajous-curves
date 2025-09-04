# 🔧 Configuración del Hardware

## Esquema del Circuito

### Componentes Principales
- **Microcontrolador**: ESP32 DevKit v1
- **Sensores**: 5x Fototransistores OP598 NPN
- **Resistencias**: 5x 100kΩ (pull-down)
- **Fuente láser**: LED de 635nm (rojo)
- **Protoboard**: Para prototipado rápido

### Conexiones Detalladas

#### Fototransistores → ESP32
| Sensor   | Color   | Pin ESP32 | Pin ADC | Coordenadas |
|----------|---------|-----------|---------|-------------|
| Sensor 1 | Azul    | GPIO 39   | ADC1_3  | (0.2, 0.0)  |
| Sensor 2 | Verde   | GPIO 36   | ADC1_0  | (0.0, 1.0)  |
| Sensor 3 | Amarillo| GPIO 34   | ADC1_6  | (0.47, 0.6) |
| Sensor 4 | Naranja | GPIO 35   | ADC1_7  | (0.8, 0.0)  |
| Sensor 5 | Rojo    | GPIO 4    | ADC2_0  | (1.0, 1.0)  |

#### Configuración de Alimentación
- **VCC**: 3.3V desde ESP32
- **GND**: Tierra común con ESP32
- **Configuración ADC**: 12-bit (0-4095)
- **Atenuación**: 11dB para rango completo (0-3.3V)


## Especificaciones Técnicas

### OP598 Fototransistor
- **Tipo**: NPN Silicon Phototransistor
- **Paquete**: T-1¾ (5mm)
- **Longitud de onda pico**: 880nm
- **Sensibilidad espectral**: 400-1100nm
- **Corriente oscura**: < 100nA
- **Tiempo de respuesta**: 15μs

### ESP32 ADC
- **Resolución**: 12-bit (0-4095)
- **Voltaje de referencia**: 3.3V
- **Frecuencia de muestreo**: Hasta 1MHz
- **Canales disponibles**: ADC1 (8 canales), ADC2 (10 canales)


### Valores de Referencia
- **Oscuridad**: ~0-10 ADC counts
- **Saturación**: ~3900-4095 ADC counts
- **Frecuencia de muestreo**: 100Hz (10ms por muestra)

## Troubleshooting

### Problemas Comunes
1. **Lecturas errática**: Verificar conexiones y resistencias
2. **Saturación**: Reducir intensidad del láser

### Tips de Instalación
- Mantener cables cortos para reducir ruido
- Usar breadboard de buena calidad
- Proteger sensores de luz ambiente
- Verificar polaridad de los fototransistores

## Referencias
- [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- [OP598 Datasheet](https://www.ttelectronics.com/TTElectronics/media/ProductFiles/Optoelectronics/Datasheets/OP598.pdf)
