"""
Sensor Array Data Acquisition System
====================================

Sistema de adquisicion de datos para un arreglo de 5 fototransistores OP598
conectados a un ESP32. Este codigo captura las lecturas de los sensores y
las emite por puerto serie en formato CSV para que la PC las guarde.

Configuración del Hardware:
- 5x Fototransistores OP598 NPN
- Resistencias pull-down de 100kΩ
- ESP32 con MicroPython v1.22.2
- Frecuencia de muestreo: 10 Hz (configurable)

Coordenadas espaciales de los sensores:
- Azul: (0.2, 0.0) - Pin 39
- Verde: (0.0, 1.0) - Pin 36  
- Amarillo: (0.47, 0.6) - Pin 34
- Naranja: (0.8, 0.0) - Pin 35
- Rojo: (1.0, 1.0) - Pin 4

Autor: Juan Jxddd
Fecha: 2024
"""

from machine import Pin, ADC
import time

# =============================================================================
# CONFIGURACIÓN DE HARDWARE
# =============================================================================

# Configuración de pines ADC para cada sensor
# Mapeo: Sensor -> (Pin GPIO, Coordenadas espaciales)
SENSOR_CONFIG = {
    'azul': {'pin': 39, 'coords': (0.2, 0.0)},
    'verde': {'pin': 36, 'coords': (0.0, 1.0)},
    'amarillo': {'pin': 34, 'coords': (0.47, 0.6)},
    'naranja': {'pin': 35, 'coords': (0.8, 0.0)},
    'rojo': {'pin': 4, 'coords': (1.0, 1.0)}
}
SENSOR_ORDER = ("azul", "verde", "amarillo", "naranja", "rojo")

# Inicializar ADCs
print("Inicializando sensores...")
sensors = {}
for sensor_name in SENSOR_ORDER:
    config = SENSOR_CONFIG[sensor_name]
    sensors[sensor_name] = ADC(Pin(config['pin']))
    print(f"  {sensor_name}: Pin {config['pin']} -> {config['coords']}")

# =============================================================================
# CONFIGURACIÓN ADC
# =============================================================================

def configure_adc_attenuation(adc_dict):
    """
    Configura la atenuación de los ADCs para el rango completo 0-3.3V
    
    Args:
        adc_dict: Diccionario de objetos ADC
    """
    print("Configurando atenuación ADC...")
    
    for sensor_name in SENSOR_ORDER:
        adc = adc_dict[sensor_name]
        try:
            adc.atten(ADC.ATTN_11DB)  # 11dB attenuation para 0-3.3V
            print(f"  {sensor_name}: ATTN_11DB configurado")
        except ValueError:
            # Fallback para versiones que requieren valor numérico
            adc.atten(3)  # Equivalente a 11dB
            print(f"  {sensor_name}: Atenuación numérica (3) configurado")

configure_adc_attenuation(sensors)

SAMPLE_RATE_HZ = 10  # Frecuencia de muestreo en Hz
SAMPLE_INTERVAL = 1.0 / SAMPLE_RATE_HZ  # Intervalo entre muestras

# =============================================================================
# FUNCIONES DE ADQUISICIÓN
# =============================================================================

def read_all_sensors(sensor_dict):
    """
    Lee todos los sensores simultáneamente
    
    Args:
        sensor_dict: Diccionario de objetos ADC
        
    Returns:
        dict: Diccionario con las lecturas de cada sensor
    """
    readings = {}
    for sensor_name, adc in sensor_dict.items():
        readings[sensor_name] = adc.read()
    return readings

def display_readings(readings, timestamp):
    """
    Muestra las lecturas en consola con formato visual
    
    Args:
        readings: Diccionario con lecturas de sensores
        timestamp: Tiempo transcurrido desde el inicio
    """
    print(f"# [T: {timestamp:.1f}s] Lecturas ADC:")
    print(f"#   Verde: {readings['verde']:4d}     Rojo: {readings['rojo']:4d}")
    print(f"#             Amarillo: {readings['amarillo']:4d}")
    print(f"#   Azul: {readings['azul']:4d}      Naranja: {readings['naranja']:4d}")


def build_csv_header():
    """
    Crea el encabezado CSV en el orden esperado por el analisis posterior.
    """
    return "tiempo," + ",".join(SENSOR_ORDER)


def format_csv_row(timestamp, readings):
    """
    Convierte una muestra a una fila CSV.
    """
    timestamp_ms = int(timestamp * 1000)
    values = [str(timestamp_ms)]
    for sensor_name in SENSOR_ORDER:
        values.append(str(readings[sensor_name]))
    return ",".join(values)

# =============================================================================
# BUCLE PRINCIPAL DE ADQUISICIÓN
# =============================================================================

def main():
    """
    Bucle principal de adquisición de datos
    """
    print(f"\n# {'='*48}")
    print("# INICIANDO ADQUISICION DE DATOS")
    print(f"# {'='*48}")
    print("# Modo de salida: streaming CSV por puerto serie")
    print(f"# Frecuencia de muestreo: {SAMPLE_RATE_HZ} Hz")
    print(f"# Intervalo de muestreo: {SAMPLE_INTERVAL:.3f} s")
    print("# Presiona Ctrl+C para detener la adquisicion")
    print(f"# {'='*48}")
    print(build_csv_header())
    
    # Variables de control
    sample_count = 0
    start_time_ms = time.ticks_ms()
    last_sync_count = 0
    
    try:
        while True:
            loop_start_ms = time.ticks_ms()
            
            # Leer todos los sensores
            readings = read_all_sensors(sensors)
            
            # Calcular tiempo transcurrido
            current_time_ms = time.ticks_diff(loop_start_ms, start_time_ms)
            current_time = current_time_ms / 1000.0
            
            print(format_csv_row(current_time, readings))
            
            sample_count += 1
            
            # Sincronización y estadísticas cada 100 muestras
            if sample_count % 100 == 0:
                elapsed_time = current_time
                actual_rate = sample_count / elapsed_time if elapsed_time > 0 else 0
                
                print(f"# [INFO] Muestras emitidas: {sample_count}")
                print(f"# [INFO] Tiempo transcurrido: {elapsed_time:.1f} s")
                print(f"# [INFO] Frecuencia real: {actual_rate:.2f} Hz")
                
                last_sync_count = sample_count
            
            # Control de frecuencia de muestreo
            loop_elapsed_ms = time.ticks_diff(time.ticks_ms(), loop_start_ms)
            sleep_time_ms = max(0, int(SAMPLE_INTERVAL * 1000) - loop_elapsed_ms)
            
            if sleep_time_ms > 0:
                time.sleep_ms(sleep_time_ms)
            elif loop_elapsed_ms > int(SAMPLE_INTERVAL * 1100):  # Si nos atrasamos más del 10%
                print(
                    "# [WARNING] Muestreo lento: {}ms > {}ms".format(
                        loop_elapsed_ms,
                        int(SAMPLE_INTERVAL * 1000),
                    )
                )
                
    except KeyboardInterrupt:
        # Finalización controlada
        total_time_ms = time.ticks_diff(time.ticks_ms(), start_time_ms)
        total_time = total_time_ms / 1000.0
        final_rate = sample_count / total_time if total_time > 0 else 0
        
        print(f"# {'='*48}")
        print("# ADQUISICION FINALIZADA")
        print(f"# {'='*48}")
        print(f"# Total de muestras: {sample_count}")
        print(f"# Tiempo total: {total_time:.1f} s")
        print(f"# Frecuencia promedio: {final_rate:.2f} Hz")
        print("# Datos emitidos por serial")
        print(f"# {'='*48}")
        
    except Exception as e:
        print(f"# [ERROR] Error inesperado: {e}")
        print("# Datos parciales emitidos por serial")

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    main()
