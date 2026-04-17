import board
import busio
import digitalio
import pwmio
import time
import math

# ── MPR121 ────────────────────────────────────────────────────────────────────
MPR121_ADDR = 0x5A

def mpr121_init(i2c):
    while not i2c.try_lock():
        pass
    i2c.writeto(MPR121_ADDR, bytes([0x80, 0x63]))
    i2c.unlock()
    time.sleep(0.001)

    while not i2c.try_lock():
        pass
    i2c.writeto(MPR121_ADDR, bytes([0x5E, 0x00]))
    for ch in range(6):
        i2c.writeto(MPR121_ADDR, bytes([0x41 + ch * 2, 6]))
        i2c.writeto(MPR121_ADDR, bytes([0x42 + ch * 2, 3]))
    i2c.writeto(MPR121_ADDR, bytes([0x5C, 0x10]))
    i2c.writeto(MPR121_ADDR, bytes([0x5D, 0x24]))
    i2c.writeto(MPR121_ADDR, bytes([0x5E, 0x0C]))
    i2c.unlock()

def mpr121_touched(i2c):
    while not i2c.try_lock():
        pass
    i2c.writeto(MPR121_ADDR, bytes([0x00]))
    result = bytearray(2)
    i2c.readfrom_into(MPR121_ADDR, result)
    i2c.unlock()
    return (result[1] << 8) | result[0]

# ── HCSR04 ───────────────────────────────────────────────────────────────────
trig = digitalio.DigitalInOut(board.GP17)
trig.direction = digitalio.Direction.OUTPUT

echo = digitalio.DigitalInOut(board.GP16)
echo.direction = digitalio.Direction.INPUT

def get_distance():
    trig.value = False
    time.sleep(0.000002)
    trig.value = True
    time.sleep(0.000010)
    trig.value = False

    timeout = time.monotonic_ns() + 30_000_000
    while not echo.value:
        if time.monotonic_ns() > timeout:
            return 999
    time1 = time.monotonic_ns()

    timeout = time.monotonic_ns() + 30_000_000
    while echo.value:
        if time.monotonic_ns() > timeout:
            return 999
    time2 = time.monotonic_ns()

    duration_s = (time2 - time1) / 1_000_000_000
    return (duration_s * 34300) / 2

def distance_to_delay(dist_cm):
    dist_cm = max(5, min(dist_cm, 100))
    ratio = (dist_cm - 5) / (100 - 5)
    return 0.05 + ratio * (0.5 - 0.05)

# ── LEDs ───────────────────────────────────────────────────────────────────
led1 = pwmio.PWMOut(board.GP26, frequency=1000, duty_cycle=0)
led2 = pwmio.PWMOut(board.GP27, frequency=1000, duty_cycle=0)
led3 = pwmio.PWMOut(board.GP28, frequency=1000, duty_cycle=0)
leds = [led1, led2, led3]

led_phase = 0.0
LED_PHASE_OFFSETS = [2 * math.pi * i / 3 for i in range(3)]

def update_leds(phase):
    for i, led in enumerate(leds):
        angle = (phase - LED_PHASE_OFFSETS[i]) % (2 * math.pi)
        brightness = max(0.0, math.sin(angle))
        led.duty_cycle = int(brightness * 65535)

LED_CYCLE_PERIOD = 3.0
led_last_update = time.monotonic()
led_delay = 0.25

distance_accumulator = 0.0
current_distance = 100
smoothed_distance = 100

# ── Stepper motors ─────────────────────────────────────────────────────────────
MOTOR_PIN_NAMES = [
    [board.GP0,  board.GP1,  board.GP2,  board.GP3],
    [board.GP4,  board.GP5,  board.GP6,  board.GP7],
    [board.GP8,  board.GP9,  board.GP10, board.GP11],
    [board.GP12, board.GP13, board.GP14, board.GP15],
]

arrSeq = [
    [0, 0, 0, 1],
    [0, 0, 1, 1],
    [0, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 0],
    [1, 1, 0, 0],
    [1, 0, 0, 0],
    [1, 0, 0, 1],
]

def make_pins(pin_names):
    pins = []
    for name in pin_names:
        p = digitalio.DigitalInOut(name)
        p.direction = digitalio.Direction.OUTPUT
        pins.append(p)
    return pins

stepper_pins = [make_pins(names) for names in MOTOR_PIN_NAMES]
seq_pointers = [[0, 1, 2, 3, 4, 5, 6, 7] for _ in MOTOR_PIN_NAMES]
directions   = [1] * len(MOTOR_PIN_NAMES)
step_counts  = [0] * len(MOTOR_PIN_NAMES)

SLOW_DELAY       = 0.003
FAST_DELAY       = 0.001
STEPS_PER_SWING  = 4096 * 3
STEPS_TOUCH_CURL = int(STEPS_PER_SWING * 1.5)

last_step_time = [time.monotonic()] * len(MOTOR_PIN_NAMES)

# ── motors sequence states ──────────────────────────────────────────────────────
phase_config = [
    [(0,  1)],
    [(3,  1)],
    [(1,  1)],
    [(1, -1), (2, 1)],
]

current_phase = 0
phase_done    = [False] * len(MOTOR_PIN_NAMES)

# ── return legs/motors to home ──────────────────────────────────────────────────────────────
homing      = False
home_steps  = [0] * len(MOTOR_PIN_NAMES)
home_dirs   = [0] * len(MOTOR_PIN_NAMES)
home_reason = "sequence"

def start_phase(phase):
    global current_phase, phase_done
    current_phase = phase
    phase_done = [False] * len(MOTOR_PIN_NAMES)
    for motor_idx, direction in phase_config[phase]:
        directions[motor_idx] = direction
        step_counts[motor_idx] = 0
        last_step_time[motor_idx] = time.monotonic()

def start_homing(reason="sequence"):
    global homing, home_steps, home_dirs, home_reason
    homing = True
    home_reason = reason
    now = time.monotonic()
    for i in range(len(MOTOR_PIN_NAMES)):
        home_steps[i] = step_counts[i]
        home_dirs[i] = -directions[i] if step_counts[i] != 0 else 0
        step_counts[i] = 0
        last_step_time[i] = now

start_phase(0)

# ── Touch state ─────────────────────────────────────────────────────
TOUCH_IDLE    = 0
TOUCH_CURLING = 1
TOUCH_HOMING  = 2

touch_state = [TOUCH_IDLE] * len(MOTOR_PIN_NAMES)
touch_steps = [0] * len(MOTOR_PIN_NAMES)

touch_interrupted = False

# ── I2C ──────────────────────────────────────────────────────────────────
i2c = busio.I2C(scl=board.GP21, sda=board.GP20, frequency=400_000)
mpr121_init(i2c)

# ── Stepper helpers ───────────────────────────────────────────────────────────
def stepper_step(motor_idx, direction):
    seq_pointers[motor_idx] = (
        seq_pointers[motor_idx][direction:] +
        seq_pointers[motor_idx][:direction]
    )
    for a in range(4):
        stepper_pins[motor_idx][a].value = arrSeq[seq_pointers[motor_idx][0]][a]

def stepper_off(motor_idx):
    for pin in stepper_pins[motor_idx]:
        pin.value = False

def motor_ready(motor_idx, delay, now):
    return (now - last_step_time[motor_idx]) >= delay

# ── Main loop ─────────────────────────────────────────────────────────────────

while True:
    now = time.monotonic()

    # ── LEDs fade in/out + distance sensor ──────────────────────────────────────────────
    dt = now - led_last_update
    led_last_update = now
    distance_accumulator += dt

    if distance_accumulator >= 0.05:
        raw_distance = get_distance()

        if raw_distance == 999:
            raw_distance = 100

        current_distance = raw_distance
        smoothed_distance = 0.7 * smoothed_distance + 0.3 * current_distance

        led_delay = distance_to_delay(smoothed_distance)
        distance_accumulator = 0.0

    max_delay = 0.5
    speed_ratio = max_delay / led_delay
    phase_speed = (2 * math.pi / LED_CYCLE_PERIOD) * speed_ratio
    led_phase = (led_phase + phase_speed * dt) % (2 * math.pi)
    update_leds(led_phase)

    # ── Read touch sensor ─────────────────────────────────────────────────────
    status = mpr121_touched(i2c)

    electrode_touched = {
        1: bool(status & (1 << 2)),  # motor 2 ← electrode 2
        2: bool(status & (1 << 3)),  # motor 3 ← electrode 3
    }

    newly_interrupted = False
    for i in [1, 2]:
        touched = electrode_touched[i]

        if touched:
            if touch_state[i] == TOUCH_IDLE:
                # leg touched = start curl
                if not touch_interrupted:
                    start_homing(reason="touch")
                touch_state[i] = TOUCH_CURLING
                touch_steps[i] = 0
                directions[i] = 1
                last_step_time[i] = now
                newly_interrupted = True

            elif touch_state[i] == TOUCH_HOMING:
                # leg retouched = recurl
                touch_state[i] = TOUCH_CURLING
                directions[i] = 1
                last_step_time[i] = now

        else:
            # leg released = return motor to home
            if touch_state[i] == TOUCH_CURLING:
                touch_state[i] = TOUCH_HOMING
                directions[i] = -1
                last_step_time[i] = now

    if newly_interrupted:
        touch_interrupted = True

    # ── Motor movement ────────────────────────────────────────────────────────
    if touch_interrupted:
        if homing:
            all_home = True
            for i in range(len(MOTOR_PIN_NAMES)):
                if home_steps[i] != 0:
                    all_home = False
                    if motor_ready(i, FAST_DELAY, now):
                        stepper_step(i, home_dirs[i])
                        home_steps[i] -= 1
                        last_step_time[i] = now
            if all_home:
                homing = False

        if not homing:
            any_active = False
            for i in [1, 2]:
                if touch_state[i] == TOUCH_CURLING:
                    any_active = True
                    if motor_ready(i, FAST_DELAY, now):
                        stepper_step(i, directions[i])
                        touch_steps[i] += 1
                        step_counts[i] = touch_steps[i]
                        last_step_time[i] = now

                        if touch_steps[i] >= STEPS_TOUCH_CURL:
                            # return home once full curl done
                            touch_state[i] = TOUCH_HOMING
                            directions[i] = -1
                            last_step_time[i] = now

                elif touch_state[i] == TOUCH_HOMING:
                    any_active = True
                    if motor_ready(i, FAST_DELAY, now):
                        stepper_step(i, directions[i])
                        touch_steps[i] -= 1
                        step_counts[i] = touch_steps[i]
                        last_step_time[i] = now

                        if touch_steps[i] <= 0:
                            touch_steps[i] = 0
                            step_counts[i] = 0
                            touch_state[i] = TOUCH_IDLE

            if not any_active and touch_state[1] == TOUCH_IDLE and touch_state[2] == TOUCH_IDLE:
                # no more touches -> restart sequence from beginning
                touch_interrupted = False
                start_phase(0)

    else:
        if homing:
            all_home = True
            for i in range(len(MOTOR_PIN_NAMES)):
                if home_steps[i] != 0:
                    all_home = False
                    if motor_ready(i, SLOW_DELAY, now):
                        stepper_step(i, home_dirs[i])
                        home_steps[i] -= 1
                        last_step_time[i] = now
            if all_home:
                homing = False
                start_phase(0)

        else:
            active_motors = [m for m, d in phase_config[current_phase]]

            for i in active_motors:
                if motor_ready(i, SLOW_DELAY, now):
                    stepper_step(i, directions[i])
                    step_counts[i] += 1
                    last_step_time[i] = now

                    if step_counts[i] >= STEPS_PER_SWING:
                        phase_done[i] = True

            if all(phase_done[i] for i in active_motors):
                next_phase = current_phase + 1
                if next_phase >= len(phase_config):
                    start_homing(reason="sequence")
                else:
                    start_phase(next_phase)