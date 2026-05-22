"""
ESP32 MicroPython LED pulse controller with OP598 capture support.

Send commands over the serial REPL stdin, one per line:
  set duty 512
  set freq 1000
  pulse 50 1023
  train 5 500 50 800
  sensor status
  sensor sample 20 1ms
  sensor pulse_profile 20 1023 20 40 1000
  sensor train_profile 5 1000 40 1023 30 50 1000
  sensor random_train_profile 10 1800 2100 40 1023 30 50 1000
  off
  status
"""

from machine import ADC, Pin, PWM
import sys
import time

try:
    import urandom
except ImportError:
    urandom = None


LED_PIN = 17
SENSOR_PIN = 36
SENSOR_NAME = "verde"
ONBOARD_LED_PIN = 2
ONBOARD_LED_OFF_VALUE = 0
ONBOARD_LED_ON_VALUE = 1
DEFAULT_FREQ_HZ = 1000
DEFAULT_DUTY = 0
MAX_DUTY = 1023
DEFAULT_SAMPLE_US = 1000
ADC_ATTEN_FALLBACK = 3


led_pwm = PWM(Pin(LED_PIN, Pin.OUT), freq=DEFAULT_FREQ_HZ, duty=DEFAULT_DUTY)
sensor_adc = ADC(Pin(SENSOR_PIN))
onboard_led = Pin(ONBOARD_LED_PIN, Pin.OUT)
current_freq = DEFAULT_FREQ_HZ
current_duty = DEFAULT_DUTY
last_sensor_adc = 0


def configure_sensor_adc():
    try:
        sensor_adc.atten(ADC.ATTN_11DB)
    except (AttributeError, ValueError):
        sensor_adc.atten(ADC_ATTEN_FALLBACK)


configure_sensor_adc()


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


def data(prefix, **fields):
    parts = [prefix]
    for key in sorted(fields):
        parts.append("{}={}".format(key, fields[key]))
    print(" ".join(parts))


def clamp_duty(value):
    return max(0, min(MAX_DUTY, int(value)))


def safe_sleep_us(value):
    if value > 0:
        time.sleep_us(int(value))


def read_sensor_adc():
    global last_sensor_adc
    last_sensor_adc = sensor_adc.read()
    return last_sensor_adc


def parse_time_token(token, default_unit):
    value = str(token).strip().lower()
    if value.endswith("us"):
        return max(0, int(value[:-2]))
    if value.endswith("ms"):
        return max(0, int(value[:-2])) * 1000
    scale = 1000 if default_unit == "ms" else 1
    return max(0, int(value)) * scale


def parse_optional_unit(value_token, unit_token, default_unit):
    if unit_token == "us":
        return max(0, int(value_token))
    if unit_token == "ms":
        return max(0, int(value_token)) * 1000
    return parse_time_token(value_token, default_unit)


def status_label(led_on, start_offsets_us, end_offsets_us, current_us):
    pulse_index = -1
    phase = "post"
    for index in range(len(start_offsets_us)):
        start_us = start_offsets_us[index]
        end_us = end_offsets_us[index]
        if current_us < start_us:
            phase = "pre" if index == 0 else "gap"
            return phase, pulse_index
        if current_us < end_us:
            return "pulse", index
        pulse_index = index
    return phase, pulse_index


def random_between(min_value, max_value):
    if max_value <= min_value:
        return min_value
    span = max_value - min_value + 1
    if urandom is not None:
        return min_value + (urandom.getrandbits(30) % span)
    now = time.ticks_us()
    return min_value + (now % span)


def build_profile_offsets(periods_ms, duration_ms, pre_ms):
    starts = []
    ends = []
    start_ms = max(0, int(pre_ms))
    duration_ms = max(0, int(duration_ms))
    for period_ms in periods_ms:
        starts.append(start_ms * 1000)
        ends.append((start_ms + duration_ms) * 1000)
        start_ms += max(0, int(period_ms))
    return starts, ends


def emit_profile_rows(command_name, start_offsets_us, end_offsets_us, total_us, sample_us, duty):
    sample_us = max(100, int(sample_us))
    previous_duty = current_duty
    event_index = 0
    event_points = []
    for index in range(len(start_offsets_us)):
        event_points.append((start_offsets_us[index], 1, index))
        event_points.append((end_offsets_us[index], 0, index))

    data(
        "SENSOR_HEADER",
        command=command_name,
        fields="index,t_us,adc,led,phase,pulse_index",
    )

    started_at = time.ticks_us()
    sample_index = 0
    led_state = 0
    led_pwm.duty(previous_duty)

    while True:
        now_us = time.ticks_diff(time.ticks_us(), started_at)
        while event_index < len(event_points) and now_us >= event_points[event_index][0]:
            next_state = event_points[event_index][1]
            led_state = next_state
            led_pwm.duty(duty if led_state else previous_duty)
            event_index += 1

        adc_value = read_sensor_adc()
        phase, pulse_index = status_label(led_state, start_offsets_us, end_offsets_us, now_us)
        data(
            "SENSOR_ROW",
            adc=adc_value,
            index=sample_index,
            led=led_state,
            phase=phase,
            pulse_index=pulse_index,
            t_us=now_us,
        )
        sample_index += 1

        if now_us >= total_us:
            break

        remaining_us = sample_us - (time.ticks_diff(time.ticks_us(), started_at) - now_us)
        if remaining_us > 0:
            safe_sleep_us(min(remaining_us, sample_us))

    led_pwm.duty(previous_duty)
    return sample_index


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


def sensor_status():
    ack(
        "sensor_status",
        adc_pin=SENSOR_PIN,
        last_adc=read_sensor_adc(),
        led_pin=LED_PIN,
        sensor_name=SENSOR_NAME,
    )


def sensor_sample(count, delay_token, unit_token=None):
    count = max(0, int(count))
    delay_us = parse_optional_unit(delay_token, unit_token, "us")
    data("SENSOR_HEADER", command="sensor_sample", fields="index,t_us,adc,led,phase,pulse_index")
    started_at = time.ticks_us()
    for index in range(count):
        now_us = time.ticks_diff(time.ticks_us(), started_at)
        data(
            "SENSOR_ROW",
            adc=read_sensor_adc(),
            index=index,
            led=1 if current_duty > 0 else 0,
            phase="steady",
            pulse_index=-1,
            t_us=now_us,
        )
        if index != count - 1:
            safe_sleep_us(delay_us)
    ack("sensor_sample", count=count, delay_us=delay_us)


def sensor_pulse_profile(duration_ms, duty, pre_ms, post_ms, sample_us):
    duration_ms = max(0, int(duration_ms))
    duty = clamp_duty(duty)
    pre_ms = max(0, int(pre_ms))
    post_ms = max(0, int(post_ms))
    sample_us = max(100, int(sample_us))
    starts, ends = build_profile_offsets([duration_ms], duration_ms, pre_ms)
    total_us = (pre_ms + duration_ms + post_ms) * 1000
    samples = emit_profile_rows("sensor_pulse_profile", starts, ends, total_us, sample_us, duty)
    ack(
        "sensor_pulse_profile",
        duration_ms=duration_ms,
        duty=duty,
        post_ms=post_ms,
        pre_ms=pre_ms,
        sample_us=sample_us,
        samples=samples,
    )


def sensor_train_profile(count, period_ms, duration_ms, duty, pre_ms, post_ms, sample_us):
    count = max(0, int(count))
    period_ms = max(1, int(period_ms))
    duration_ms = max(0, int(duration_ms))
    duty = clamp_duty(duty)
    pre_ms = max(0, int(pre_ms))
    post_ms = max(0, int(post_ms))
    sample_us = max(100, int(sample_us))

    if duration_ms > period_ms:
        err("duration_ms_must_be_less_or_equal_period_ms")
        return

    periods_ms = [period_ms] * count
    starts, ends = build_profile_offsets(periods_ms, duration_ms, pre_ms)
    total_us = (pre_ms + post_ms + max(0, count - 1) * period_ms + duration_ms) * 1000
    samples = emit_profile_rows("sensor_train_profile", starts, ends, total_us, sample_us, duty)
    ack(
        "sensor_train_profile",
        count=count,
        duration_ms=duration_ms,
        duty=duty,
        period_ms=period_ms,
        post_ms=post_ms,
        pre_ms=pre_ms,
        sample_us=sample_us,
        samples=samples,
    )


def sensor_random_train_profile(
    count,
    min_period_ms,
    max_period_ms,
    duration_ms,
    duty,
    pre_ms,
    post_ms,
    sample_us,
):
    count = max(0, int(count))
    min_period_ms = max(1, int(min_period_ms))
    max_period_ms = max(min_period_ms, int(max_period_ms))
    duration_ms = max(0, int(duration_ms))
    duty = clamp_duty(duty)
    pre_ms = max(0, int(pre_ms))
    post_ms = max(0, int(post_ms))
    sample_us = max(100, int(sample_us))

    periods_ms = []
    for _index in range(count):
        period_ms = random_between(min_period_ms, max_period_ms)
        if duration_ms > period_ms:
            period_ms = duration_ms
        periods_ms.append(period_ms)

    starts, ends = build_profile_offsets(periods_ms, duration_ms, pre_ms)
    total_us = (pre_ms + post_ms + sum(periods_ms[:-1]) + duration_ms) * 1000 if count else (pre_ms + post_ms) * 1000
    samples = emit_profile_rows(
        "sensor_random_train_profile",
        starts,
        ends,
        total_us,
        sample_us,
        duty,
    )
    ack(
        "sensor_random_train_profile",
        count=count,
        duration_ms=duration_ms,
        duty=duty,
        max_period_ms=max_period_ms,
        min_period_ms=min_period_ms,
        post_ms=post_ms,
        pre_ms=pre_ms,
        sample_us=sample_us,
        samples=samples,
    )


def handle_onboard(parts):
    if len(parts) != 2:
        err("unknown_boardled_command")


def handle_sensor(parts):
    if len(parts) < 2:
        err("unknown_sensor_command")
        return
    if parts[1] == "status" and len(parts) == 2:
        sensor_status()
    elif parts[1] == "sample" and len(parts) in (4, 5):
        sensor_sample(parts[2], parts[3], parts[4] if len(parts) == 5 else None)
    elif parts[1] == "pulse_profile" and len(parts) == 7:
        sensor_pulse_profile(parts[2], parts[3], parts[4], parts[5], parts[6])
    elif parts[1] == "train_profile" and len(parts) == 9:
        sensor_train_profile(parts[2], parts[3], parts[4], parts[5], parts[6], parts[7], parts[8])
    elif parts[1] == "random_train_profile" and len(parts) == 10:
        sensor_random_train_profile(
            parts[2], parts[3], parts[4], parts[5], parts[6], parts[7], parts[8], parts[9]
        )
    else:
        err("unknown_sensor_command")
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
        elif parts[0] == "sensor":
            handle_sensor(parts)
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
