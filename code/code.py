# Stepper motors with MPR121 touch sensor + HC-SR04 controlling LEDs
# MPR121 pins 0-2 → motor 1 fast
# MPR121 pins 3-5 → motor 2 fast
# MPR121 pins 6-8 → motor 3 fast
# nothing touched → all motors slow
# HC-SR04 distance → LED alternating speed (near=fast, far=slow)

import board
import busio
import digitalio
import time
import synthio
import audiopwmio
import audiomixer
import array
import math

# ── Synthio audio via PAM8302A ────────────────────────────────────────────────
audio = audiopwmio.PWMAudioOut(board.GP18)
mixer = audiomixer.Mixer(channel_count=1, sample_rate=44100, buffer_size=4096)
synth = synthio.Synthesizer(channel_count=1, sample_rate=44100)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.5

envelope = synthio.Envelope(
    attack_time=0.4,
    sustain_level=0.6,
    release_time=1.2,
)

# Sine wave — smoothest, most ethereal tone
wave_sine = array.array('h',
    [int(32767 * math.sin(2 * math.pi * i / 512)) for i in range(512)]
)

current_note = None

def distance_to_midi(dist_cm):
    """Map 5–100 cm to a pentatonic scale (always harmonious)."""
    pentatonic = [45, 48, 50, 52, 55, 57, 60, 62, 64, 67]  # low A to G, two octaves
    dist_cm = max(5, min(dist_cm, 100))
    ratio = (dist_cm - 5) / (100 - 5)
    idx = int((1 - ratio) * (len(pentatonic) - 1))  # close = higher note
    return pentatonic[idx]

def set_tone(midi_note):
    global current_note
    if current_note is not None:
        synth.release(current_note)
    if midi_note is None:
        current_note = None
        return
    current_note = synthio.Note(
        frequency=synthio.midi_to_hz(midi_note),
        waveform=wave_sine,
        envelope=envelope,
    )
    synth.press(current_note)
    
MPR121_ADDR = 0x5A

def mpr121_init(i2c):
    while not i2c.try_lock():
        pass
    i2c.writeto(MPR121_ADDR, bytes([0x80, 0x63]))  # soft reset
    i2c.unlock()
    time.sleep(0.001)

    while not i2c.try_lock():
        pass
    i2c.writeto(MPR121_ADDR, bytes([0x5E, 0x00]))  # stop mode
    for ch in range(9):
        i2c.writeto(MPR121_ADDR, bytes([0x41 + ch * 2, 12]))  # touch threshold
        i2c.writeto(MPR121_ADDR, bytes([0x42 + ch * 2, 6]))   # release threshold
    i2c.writeto(MPR121_ADDR, bytes([0x5C, 0x10]))  # analog frontend config
    i2c.writeto(MPR121_ADDR, bytes([0x5D, 0x24]))  # filter config
    i2c.writeto(MPR121_ADDR, bytes([0x5E, 0x0C]))  # activate, out of stop mode
    i2c.unlock()

def mpr121_touched(i2c):
    while not i2c.try_lock():
        pass
    i2c.writeto(MPR121_ADDR, bytes([0x00]))
    result = bytearray(2)
    i2c.readfrom_into(MPR121_ADDR, result)
    i2c.unlock()
    return (result[1] << 8) | result[0]

# ── HC-SR04 ───────────────────────────────────────────────────────────────────
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

    timeout = time.monotonic_ns() + 30_000_000  # 30 ms timeout
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
    """Map 5–100 cm → 0.05–0.5 s LED alternating delay."""
    dist_cm = max(5, min(dist_cm, 100))
    ratio = (dist_cm - 5) / (100 - 5)
    return 0.05 + ratio * (0.5 - 0.05)

# ── LEDs ──────────────────────────────────────────────────────────────────────
led1 = digitalio.DigitalInOut(board.GP15)
led1.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.GP14)
led2.direction = digitalio.Direction.OUTPUT

# ── Stepper setup ─────────────────────────────────────────────────────────────
MOTOR_PIN_NAMES = [
    [board.GP0,  board.GP1,  board.GP2,  board.GP3],
    [board.GP4,  board.GP5,  board.GP6,  board.GP7],
    [board.GP8,  board.GP9,  board.GP10, board.GP11],
]

MOTOR_MASKS = [
    0x007,   # electrodes 0-2 → motor 1
    0x038,   # electrodes 3-5 → motor 2
    0x1C0,   # electrodes 6-8 → motor 3
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

SLOW_DELAY      = 0.003
FAST_DELAY      = 0.001
STEPS_PER_SWING = 4096 * 3

# ── I2C init ──────────────────────────────────────────────────────────────────
i2c = busio.I2C(scl=board.GP21, sda=board.GP20, frequency=400_000)
mpr121_init(i2c)

# ── Stepper helpers ───────────────────────────────────────────────────────────
def stepper_step(motor_idx, direction, delay):
    seq_pointers[motor_idx] = (
        seq_pointers[motor_idx][direction:] +
        seq_pointers[motor_idx][:direction]
    )
    for a in range(4):
        stepper_pins[motor_idx][a].value = arrSeq[seq_pointers[motor_idx][0]][a]
    time.sleep(delay)

def stepper_off(motor_idx):
    for pin in stepper_pins[motor_idx]:
        pin.value = False

# ── LED & distance state ──────────────────────────────────────────────────────
led_state       = False          # False = led1 on, led2 off
led_last_toggle = time.monotonic()
led_delay       = 0.25           # initial delay, updated by distance

# ── Main loop ─────────────────────────────────────────────────────────────────
print("Running — touch → motor speed | distance → LED blink rate")

while True:
    now = time.monotonic()

    if now - led_last_toggle >= led_delay:
        led_state = not led_state
        led1.value = led_state
        led2.value = not led_state

        dist = get_distance()
        led_delay = distance_to_delay(dist)
        led_last_toggle = now

        # ── Audio ─────────────────────────────────────────────────────────
        if dist < 999:
            set_tone(distance_to_midi(dist))
        else:
            set_tone(None)

    # ── Motors: touch sensor controls speed ───────────────────────────────────
    status = mpr121_touched(i2c)

    for i in range(len(MOTOR_PIN_NAMES)):
        delay = FAST_DELAY if (status & MOTOR_MASKS[i]) else SLOW_DELAY
        stepper_step(i, directions[i], delay)
        step_counts[i] += 1
        if step_counts[i] >= STEPS_PER_SWING:
            step_counts[i] = 0
            directions[i] = -directions[i]
