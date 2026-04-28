"""
Latency Test for ESP32 + OP598 Phototransistor
==============================================

Este script mide la latencia practica del sistema completo:

1. Se enciende un LED conectado a un pin GPIO del ESP32.
2. Se observa el cambio analogico en un fototransistor OP598.
3. Se detecta el cruce de un umbral mediante polling intensivo del ADC.
4. Se reporta la diferencia temporal en microsegundos.

La medicion resultante representa la latencia de deteccion en esta plataforma
con MicroPython. No es una medicion aislada de la respuesta intrinseca del
fototransistor.
"""

from machine import Pin, ADC
import time


# =============================================================================
# CONFIGURACION
# =============================================================================

LED_PIN = 17
SENSOR_PIN = 36

CALIBRATION_SAMPLES = 64
TRIAL_COUNT = 50
SETTLE_MS = 10
TIMEOUT_US = 5000
INTER_TRIAL_DELAY_MS = 100


# =============================================================================
# HARDWARE
# =============================================================================

led_pin = Pin(LED_PIN, Pin.OUT)
sensor_adc = ADC(Pin(SENSOR_PIN))


def configure_adc(adc):
    """
    Configura el ADC para cubrir el rango completo aproximado de 0-3.3V.
    """
    try:
        adc.atten(ADC.ATTN_11DB)
    except ValueError:
        adc.atten(3)


configure_adc(sensor_adc)


# =============================================================================
# UTILIDADES
# =============================================================================

def average_samples(adc, sample_count):
    """
    Calcula el promedio de varias muestras ADC para estabilizar la calibracion.
    """
    total = 0
    for _ in range(sample_count):
        total += adc.read()
    return total // sample_count


def median(values):
    """
    Calcula la mediana sin depender del modulo statistics.
    """
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2

    if count % 2:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2


def calibrate_threshold(adc, led):
    """
    Mide nivel oscuro y nivel iluminado para definir un umbral util.
    """
    led.value(0)
    time.sleep_ms(SETTLE_MS)
    dark_level = average_samples(adc, CALIBRATION_SAMPLES)

    led.value(1)
    time.sleep_ms(SETTLE_MS)
    lit_level = average_samples(adc, CALIBRATION_SAMPLES)

    led.value(0)
    time.sleep_ms(SETTLE_MS)

    threshold = (dark_level + lit_level) // 2
    return dark_level, lit_level, threshold


def measure_latency(adc, led, threshold):
    """
    Ejecuta una sola medicion de latencia usando polling intensivo del ADC.
    """
    led.value(0)
    time.sleep_ms(SETTLE_MS)

    start_us = time.ticks_us()
    led.value(1)

    detect_us = None
    timed_out = False

    while True:
        reading = adc.read()
        if reading >= threshold:
            detect_us = time.ticks_us()
            break

        elapsed_us = time.ticks_diff(time.ticks_us(), start_us)
        if elapsed_us >= TIMEOUT_US:
            timed_out = True
            break

    led.value(0)

    if timed_out:
        return None

    return time.ticks_diff(detect_us, start_us)


def print_configuration():
    print("=" * 60)
    print("PRUEBA DE LATENCIA - ESP32 + OP598")
    print("=" * 60)
    print("LED pin: {}".format(LED_PIN))
    print("Sensor pin: {}".format(SENSOR_PIN))
    print("Calibration samples: {}".format(CALIBRATION_SAMPLES))
    print("Trial count: {}".format(TRIAL_COUNT))
    print("Settle time: {} ms".format(SETTLE_MS))
    print("Timeout: {} us".format(TIMEOUT_US))
    print("=" * 60)


def print_summary(results, failures, dark_level, lit_level, threshold):
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print("Dark level: {}".format(dark_level))
    print("Lit level: {}".format(lit_level))
    print("Threshold: {}".format(threshold))
    print("Trials OK: {}".format(len(results)))
    print("Trials failed: {}".format(failures))

    if not results:
        print("No se obtuvieron mediciones validas.")
        return

    average_latency = sum(results) / len(results)
    print("Latency min: {} us".format(min(results)))
    print("Latency max: {} us".format(max(results)))
    print("Latency avg: {:.1f} us".format(average_latency))
    print("Latency median: {} us".format(median(results)))


def main():
    print_configuration()
    print("Asegura la alineacion del LED con el sensor antes de comenzar.")
    time.sleep_ms(1000)

    dark_level, lit_level, threshold = calibrate_threshold(sensor_adc, led_pin)

    print("\nCalibracion completada:")
    print("  Dark level: {}".format(dark_level))
    print("  Lit level: {}".format(lit_level))
    print("  Threshold: {}".format(threshold))

    if lit_level <= dark_level:
        print("\n[ERROR] El nivel iluminado no supera al nivel oscuro.")
        print("Revisa alineacion, luz ambiente y conexion del LED.")
        return

    results = []
    failures = 0

    print("\nIniciando mediciones...")
    for trial_number in range(1, TRIAL_COUNT + 1):
        latency_us = measure_latency(sensor_adc, led_pin, threshold)

        if latency_us is None:
            failures += 1
            print(
                "[{:02d}/{:02d}] timeout | dark={} lit={} threshold={}".format(
                    trial_number,
                    TRIAL_COUNT,
                    dark_level,
                    lit_level,
                    threshold,
                )
            )
        else:
            results.append(latency_us)
            print(
                "[{:02d}/{:02d}] latency={} us | dark={} lit={} threshold={}".format(
                    trial_number,
                    TRIAL_COUNT,
                    latency_us,
                    dark_level,
                    lit_level,
                    threshold,
                )
            )

        time.sleep_ms(INTER_TRIAL_DELAY_MS)

    print_summary(results, failures, dark_level, lit_level, threshold)


if __name__ == "__main__":
    main()
