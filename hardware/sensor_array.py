"""
Sensor Array Data Acquisition System
====================================

Sistema de adquisición de datos para un arreglo de 5 fototransistores OP598
conectados a un ESP32. Este código captura las lecturas de los sensores y
las guarda en formato CSV para análisis posterior.

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

Autor: Juan J
Fecha: 2024
"""

from machine import Pin, ADC
import time
import os

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

# Inicializar ADCs
print("Inicializando sensores...")
sensors = {}
for sensor_name, config in SENSOR_CONFIG.items():
    sensors[sensor_name] = ADC(Pin(config['pin']))
    print(f"  {sensor_name.capitalize()}: Pin {config['pin']} -> {config['coords']}")

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
    
    for sensor_name, adc in adc_dict.items():
        try:
            adc.atten(ADC.ATTN_11DB)  # 11dB attenuation para 0-3.3V
            print(f"  {sensor_name}: ATTN_11DB configurado")
        except ValueError:
            # Fallback para versiones que requieren valor numérico
            adc.atten(3)  # Equivalente a 11dB
            print(f"  {sensor_name}: Atenuación numérica (3) configurado")

configure_adc_attenuation(sensors)

# =============================================================================
# CONFIGURACIÓN DE ARCHIVO
# =============================================================================

# Configuración de archivo CSV
FILENAME = "sensor_data.csv"
SAMPLE_RATE_HZ = 10  # Frecuencia de muestreo en Hz
SAMPLE_INTERVAL = 1.0 / SAMPLE_RATE_HZ  # Intervalo entre muestras

# Crear encabezado CSV si el archivo no existe
def initialize_csv_file(filename):
    """
    Inicializa el archivo CSV con encabezados apropiados
    
    Args:
        filename: Nombre del archivo CSV
    """
    if filename not in os.listdir():
        print(f"Creando nuevo archivo: {filename}")
        with open(filename, "w") as f:
            header = "tiempo," + ",".join(SENSOR_CONFIG.keys()) + "\n"
            f.write(header)
    else:
        print(f"Usando archivo existente: {filename}")

initialize_csv_file(FILENAME)

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
    print(f"\n[T: {timestamp:.1f}s] Lecturas ADC:")
    print(f"  Verde: {readings['verde']:4d}     Rojo: {readings['rojo']:4d}")
    print(f"            Amarillo: {readings['amarillo']:4d}")
    print(f"  Azul: {readings['azul']:4d}      Naranja: {readings['naranja']:4d}")

def save_to_csv(filename, timestamp, readings):
    """
    Guarda las lecturas en archivo CSV
    
    Args:
        filename: Nombre del archivo CSV
        timestamp: Tiempo en segundos
        readings: Diccionario con lecturas de sensores
    """
    with open(filename, "a") as f:
        # Convertir timestamp a milisegundos para consistencia
        timestamp_ms = int(timestamp * 1000)
        
        # Crear línea CSV en el orden correcto
        values = [str(timestamp_ms)]
        for sensor_name in SENSOR_CONFIG.keys():
            values.append(str(readings[sensor_name]))
        
        line = ",".join(values) + "\n"
        f.write(line)

# =============================================================================
# BUCLE PRINCIPAL DE ADQUISICIÓN
# =============================================================================

def main():
    """
    Bucle principal de adquisición de datos
    """
    print(f"\n{'='*50}")
    print("INICIANDO ADQUISICIÓN DE DATOS")
    print(f"{'='*50}")
    print(f"Archivo de salida: {FILENAME}")
    print(f"Frecuencia de muestreo: {SAMPLE_RATE_HZ} Hz")
    print(f"Intervalo de muestreo: {SAMPLE_INTERVAL:.3f} s")
    print("Presiona Ctrl+C para detener la adquisición")
    print(f"{'='*50}")
    
    # Variables de control
    sample_count = 0
    start_time = time.time()
    last_sync_count = 0
    
    try:
        while True:
            loop_start = time.time()
            
            # Leer todos los sensores
            readings = read_all_sensors(sensors)
            
            # Calcular tiempo transcurrido
            current_time = loop_start - start_time
            
            # Mostrar lecturas cada 10 muestras para no saturar la consola
            if sample_count % 10 == 0:
                display_readings(readings, current_time)
            
            # Guardar en archivo CSV
            save_to_csv(FILENAME, current_time, readings)
            
            sample_count += 1
            
            # Sincronización y estadísticas cada 100 muestras
            if sample_count % 100 == 0:
                samples_since_sync = sample_count - last_sync_count
                elapsed_time = current_time
                actual_rate = sample_count / elapsed_time if elapsed_time > 0 else 0
                
                print(f"\n[INFO] Muestras guardadas: {sample_count}")
                print(f"[INFO] Tiempo transcurrido: {elapsed_time:.1f} s")
                print(f"[INFO] Frecuencia real: {actual_rate:.2f} Hz")
                print(f"[INFO] Archivo: {FILENAME}")
                
                last_sync_count = sample_count
            
            # Control de frecuencia de muestreo
            loop_time = time.time() - loop_start
            sleep_time = max(0, SAMPLE_INTERVAL - loop_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif loop_time > SAMPLE_INTERVAL * 1.1:  # Si nos atrasamos más del 10%
                print(f"[WARNING] Muestreo lento: {loop_time:.3f}s > {SAMPLE_INTERVAL:.3f}s")
                
    except KeyboardInterrupt:
        # Finalización controlada
        end_time = time.time()
        total_time = end_time - start_time
        final_rate = sample_count / total_time if total_time > 0 else 0
        
        print(f"\n{'='*50}")
        print("ADQUISICIÓN FINALIZADA")
        print(f"{'='*50}")
        print(f"Total de muestras: {sample_count}")
        print(f"Tiempo total: {total_time:.1f} s")
        print(f"Frecuencia promedio: {final_rate:.2f} Hz")
        print(f"Datos guardados en: {FILENAME}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        print(f"Datos parciales guardados en: {FILENAME}")

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    main()
