"""
ESP32 MicroPython LED pulse controller.

Send commands over the serial REPL stdin, one per line:
  set duty 512
  set freq 1000
  pulse 50 1023
  train 5 500 50 800
  off
  status
"""

from machine import Pin, PWM
import sys
import time


LED_PIN = 17
ONBOARD_LED_PIN = 2
ONBOARD_LED_OFF_VALUE = 0
ONBOARD_LED_ON_VALUE = 1
DEFAULT_FREQ_HZ = 1000
DEFAULT_DUTY = 0
MAX_DUTY = 1023


led_pwm = PWM(Pin(LED_PIN, Pin.OUT), freq=DEFAULT_FREQ_HZ, duty=DEFAULT_DUTY)
onboard_led = Pin(ONBOARD_LED_PIN, Pin.OUT)
current_freq = DEFAULT_FREQ_HZ
current_duty = DEFAULT_DUTY


def onboard_off():
    onboard_led.value(ONBOARD_LED_OFF_VALUE)


def onboard_on():
    onboard_led.value(ONBOARD_LED_ON_VALUE)


onboard_off()


def ack(command, **fields):
    parts = ["OK", command]
    for key in sorted(fields):
        parts.append("{}={}".format(key, fields[key]))
    print(" ".join(parts))


def err(message):
    print("ERR message={}".format(message.replace(" ", "_")))


def clamp_duty(value):
    return max(0, min(MAX_DUTY, int(value)))


def set_duty(value):
    global current_duty
    onboard_off()
    current_duty = clamp_duty(value)
    led_pwm.duty(current_duty)
    ack("set_duty", duty=current_duty)


def set_freq(value):
    global current_freq
    onboard_off()
    current_freq = max(1, int(value))
    led_pwm.freq(current_freq)
    ack("set_freq", freq=current_freq)


def off():
    global current_duty
    current_duty = 0
    led_pwm.duty(current_duty)
    onboard_off()
    ack("off", duty=current_duty)


def pulse(duration_ms, duty):
    onboard_off()
    previous_duty = current_duty
    led_pwm.duty(clamp_duty(duty))
    time.sleep_ms(max(0, int(duration_ms)))
    led_pwm.duty(previous_duty)
    ack("pulse", duration_ms=int(duration_ms), duty=clamp_duty(duty))


def train(count, period_ms, duration_ms, duty):
    onboard_off()
    count = max(0, int(count))
    period_ms = max(1, int(period_ms))
    duration_ms = max(0, int(duration_ms))
    duty = clamp_duty(duty)

    if duration_ms > period_ms:
        err("duration_ms_must_be_less_or_equal_period_ms")
        return

    previous_duty = current_duty
    for index in range(count):
        started = time.ticks_ms()
        led_pwm.duty(duty)
        time.sleep_ms(duration_ms)
        led_pwm.duty(previous_duty)
        remaining_ms = period_ms - time.ticks_diff(time.ticks_ms(), started)
        if index != count - 1 and remaining_ms > 0:
            time.sleep_ms(remaining_ms)
    ack("train", count=count, period_ms=period_ms, duration_ms=duration_ms, duty=duty)


def status():
    ack(
        "status",
        pin=LED_PIN,
        freq=current_freq,
        duty=current_duty,
        onboard_led_pin=ONBOARD_LED_PIN,
        onboard_led_value=onboard_led.value(),
    )


def handle_onboard(parts):
    if len(parts) != 2:
        err("unknown_boardled_command")
        return
    if parts[1] == "off":
        onboard_off()
        ack("boardled", state="off", pin=ONBOARD_LED_PIN, value=onboard_led.value())
    else:
        err("unknown_boardled_command")


def handle(line):
    parts = line.strip().split()
    if not parts:
        return

    try:
        if parts[:2] == ["set", "duty"] and len(parts) == 3:
            set_duty(parts[2])
        elif parts[:2] == ["set", "freq"] and len(parts) == 3:
            set_freq(parts[2])
        elif parts[0] == "pulse" and len(parts) == 3:
            pulse(parts[1], parts[2])
        elif parts[0] == "train" and len(parts) == 5:
            train(parts[1], parts[2], parts[3], parts[4])
        elif parts[0] == "off" and len(parts) == 1:
            off()
        elif parts[0] == "boardled":
            handle_onboard(parts)
        elif parts[0] == "status" and len(parts) == 1:
            status()
        else:
            err("unknown_command")
    except Exception as exc:
        err(str(exc))


def main():
    onboard_off()
    led_pwm.duty(0)
    ack("ready", pin=LED_PIN, freq=current_freq, duty=current_duty)
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep_ms(10)
            continue
        handle(line)


try:
    main()
finally:
    led_pwm.duty(0)
    onboard_off()
