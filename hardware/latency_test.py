"""
Latency Test for ESP32 + OP598 Phototransistor
==============================================

Este script mide la latencia practica del montaje completo:

1. Se enciende un LED conectado a un pin GPIO del ESP32.
2. Se observa el cambio analogico en un fototransistor OP598.
3. Se detecta el cruce de un umbral fijo mediante polling intensivo del ADC.
4. Se registra la latencia en microsegundos.

El ESP32 solo lee y emite los datos; el procesamiento se hace en la PC.
"""

from machine import Pin, ADC
import time


# =============================================================================
# CONFIGURACION
# =============================================================================

LED_PIN = 17
SENSOR_PIN = 36

TRIAL_COUNT = 5
SETTLE_MS = 2
TIMEOUT_US = 10000
INTER_TRIAL_DELAY_MS = 20

# Duracion del destello en microsegundos. 0 = sin limite.
FLASH_PULSE_US = 500

# Umbral fijo en cuentas ADC. Ajustar segun el montaje real.
THRESHOLD_ADC = 55

# Direccion del cambio esperado: 1 si la luz sube la lectura, -1 si baja.
DIRECTION = 1


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

def crossed_threshold(reading, threshold, direction):
    """
    Evalua si la lectura ya cruzo el umbral segun la polaridad esperada.
    """
    if direction > 0:
        return reading >= threshold
    return reading <= threshold


def measure_latency(adc, led, threshold, direction):
    """
    Ejecuta una sola medicion de latencia usando polling intensivo del ADC.
    """
    led.value(0)
    time.sleep_ms(SETTLE_MS)

    start_us = time.ticks_us()
    led.value(1)

    pulse_end_us = None
    if FLASH_PULSE_US > 0:
        pulse_end_us = time.ticks_add(start_us, FLASH_PULSE_US)
    pulse_done = False

    last_reading = adc.read()
    while True:
        last_reading = adc.read()
        now_us = time.ticks_us()

        if crossed_threshold(last_reading, threshold, direction):
            led.value(0)
            return time.ticks_diff(now_us, start_us), last_reading

        if pulse_end_us is not None and not pulse_done:
            if time.ticks_diff(now_us, pulse_end_us) >= 0:
                led.value(0)
                pulse_done = True

        if time.ticks_diff(now_us, start_us) >= TIMEOUT_US:
            led.value(0)
            return None, last_reading


def direction_label(direction):
    if direction > 0:
        return "rising"
    if direction < 0:
        return "falling"
    return "unknown"


def print_configuration():
    print("=" * 60)
    print("PRUEBA DE LATENCIA - ESP32 + OP598")
    print("=" * 60)
    print("LED pin: {}".format(LED_PIN))
    print("Sensor pin: {}".format(SENSOR_PIN))
    print("Trial count: {}".format(TRIAL_COUNT))
    print("Settle time: {} ms".format(SETTLE_MS))
    print("Timeout: {} us".format(TIMEOUT_US))
    print("Flash pulse: {} us".format(FLASH_PULSE_US))
    print("Threshold ADC: {}".format(THRESHOLD_ADC))
    print("Direction: {}".format(direction_label(DIRECTION)))
    print("=" * 60)


def print_csv_header():
    print("CSV_HEADER,trial,latency_us,adc")


def print_csv_trial(trial_number, latency_us, adc_value):
    line = "CSV_ROW,{},{},{}".format(trial_number, latency_us, adc_value)
    print(line)


def main():
    print_configuration()
    print("Asegura la alineacion del LED con el sensor antes de comenzar.")
    time.sleep_ms(1000)

    print_csv_header()

    for trial_number in range(1, TRIAL_COUNT + 1):
        latency_us, trigger_reading = measure_latency(
            sensor_adc, led_pin, THRESHOLD_ADC, DIRECTION
        )
        if latency_us is None:
            print_csv_trial(trial_number, "", trigger_reading)
        else:
            print_csv_trial(trial_number, latency_us, trigger_reading)

        time.sleep_ms(INTER_TRIAL_DELAY_MS)


if __name__ == "__main__":
    main()
