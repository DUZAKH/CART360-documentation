import time
import board
import pwmio
from digitalio import DigitalInOut, Direction
import wifi
import socketpool
import struct
import os

# ----- DEBUG LED SETUP -----
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led_state = False

def blink_debug():
    global led_state
    led_state = not led_state
    led.value = led_state

# ----- WIFI SETUP -----
SSID = os.getenv("CIRCUITPY_WIFI_SSID")
PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")

wifi_connected = False
try:
    wifi.radio.connect(SSID, PASSWORD)
    print("Connected with IP:", wifi.radio.ipv4_address)
    pool = socketpool.SocketPool(wifi.radio)
    # UDP_IP = "192.168.0.17"  # replace with your receiving computer IP
    UDP_IP = "192.0.0.2"
    UDP_PORT = 8000
    sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
    wifi_connected = True
except Exception as e:
    print("Wi-Fi failed:", e)

def send_osc(address, value):
    if not wifi_connected:
        return
    addr = address.encode()
    addr += b'\x00' * (4 - len(address) % 4)
    types = b',f\x00\x00'
    data = struct.pack(">f", value)
    try:
        sock.sendto(addr + types + data, (UDP_IP, UDP_PORT))
    except OSError as e:
        print("OSC send failed:", e)

# ----- DC MOTOR SETUP -----
motor_pwm = pwmio.PWMOut(board.GP15, frequency=1000)  # PWM for speed
motor_dir = DigitalInOut(board.GP14)                  # Direction pin
motor_dir.direction = Direction.OUTPUT

def set_motor_speed(speed):
    """
    speed: -1.0 to 1.0
    Negative = backward, Positive = forward
    """
    if speed >= 0:
        motor_dir.value = True
        duty = int(min(speed * 65535, 65535))
    else:
        motor_dir.value = False
        duty = int(min(-speed * 65535, 65535))
    motor_pwm.duty_cycle = duty
    send_osc("/pico/motor", float(speed))

def move_motor_back_and_forth(duration=2.0, speed=0.5):
    """
    Move motor forward for half duration, then backward.
    duration: total seconds of back-and-forth
    speed: 0.0 to 1.0
    """
    half = duration / 2
    # Forward
    set_motor_speed(speed)
    start = time.monotonic()
    while (time.monotonic() - start) < half:
        blink_debug()
        time.sleep(0.02)
    # Backward
    set_motor_speed(-speed)
    start = time.monotonic()
    while (time.monotonic() - start) < half:
        blink_debug()
        time.sleep(0.02)
    # Stop
    set_motor_speed(0)

# ----- ULTRASONIC SENSOR SETUP -----
trigger = DigitalInOut(board.GP3)
trigger.direction = Direction.OUTPUT
echo = DigitalInOut(board.GP2)
echo.direction = Direction.INPUT

def time_pulse_us(pin, level, timeout=1000000):
    start = time.monotonic()
    while pin.value != level:
        if (time.monotonic() - start) > timeout / 1_000_000:
            return -2
    start_time = time.monotonic()
    while pin.value == level:
        if (time.monotonic() - start_time) > timeout / 1_000_000:
            break
    duration = (time.monotonic() - start_time) * 1_000_000
    return duration

def get_distance():
    trigger.value = False
    time.sleep(0.000002)
    trigger.value = True
    time.sleep(0.00001)
    trigger.value = False
    duration = time_pulse_us(echo, True)
    distance = (duration * 0.0343) / 2
    return distance

# ----- MAIN LOOP -----
threshold = 100  # cm
state = "empty"

while True:
    blink_debug()  # heartbeat LED

    # Read multiple distances and average
    readings = []
    for _ in range(5):
        d = get_distance()
        if d > 0:
            readings.append(d)
        time.sleep(0.02)
    if not readings:
        continue
    distance = sum(readings) / len(readings)
    print("Distance:", distance)

    # State machine for motor based on distance
    if distance < threshold and state == "empty":
        print("Participant detected")
        move_motor_back_and_forth(duration=2.0, speed=0.6)
        state = "occupied"
    elif distance >= threshold and state == "occupied":
        print("Participant left")
        move_motor_back_and_forth(duration=2.0, speed=0.6)
        state = "empty"

    time.sleep(0.3)