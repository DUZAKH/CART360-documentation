# Spirob tentacle controller — 4 tentacles, 4 motors
# Motor 1 (GP0-3):   inward curl for all 4 tentacles
# Motor 2 (GP4-7):   right curl for tentacles 1 & 2
# Motor 3 (GP8-11):  right curl for tentacles 3 & 4
# Motor 4 (GP12-15): outward curl for all 4 tentacles
#
# Round-robin sequence (no touch):
#   PHASE 0 — Motor 1 forward  (all tentacles curl inward)
#   PHASE 1 — Motor 4 forward  (all tentacles curl outward)
#   PHASE 2 — Motor 2 forward  (tentacles 1&2 curl right)
#   PHASE 3 — Motor 2 backward + Motor 3 forward simultaneously
#             (tentacles 3&4 curl right)
#   PHASE 4 — All motors home → repeat from phase 0
#
# Touch behaviour:
#   Touch on MPR121 electrodes 2 or 3 → interrupts sequence, homes all motors,
#     then motor 2 curls tentacles 1&2 outward with a tighter (longer) swing
#   Touch on MPR121 electrodes 4 or 5 → same but motor 3 for tentacles 3&4
#   Motors 2 & 3 can run simultaneously if both leg groups are touched
#   Release early → that motor homes; sequence restarts only when ALL
#     touch interactions are fully homed
#   Motors 1 and 4 are NOT triggered by touch
#
# HC-SR04 distance → LED blink speed + audio tone

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

wave_sine = array.array('h',
    [int(32767 * math.sin(2 * math.pi * i / 512)) for i in range(512)]
)

current_note = None

def distance_to_midi(dist_cm):
    pentatonic = [45, 48, 50, 52, 55, 57, 60, 62, 64, 67]
    dist_cm = max(5, min(dist_cm, 100))
    ratio = (dist_cm - 5) / (100 - 5)
    idx = int((1 - ratio) * (len(pentatonic) - 1))
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
    for ch in range(6):                          # electrodes 0-5 (only 2-5 used for touch)
        i2c.writeto(MPR121_ADDR, bytes([0x41 + ch * 2, 12]))
        i2c.writeto(MPR121_ADDR, bytes([0x42 + ch * 2, 6]))
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

# ── LEDs (moved to GP26, GP27) ────────────────────────────────────────────────
led1 = digitalio.DigitalInOut(board.GP26)
led1.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.GP27)
led2.direction = digitalio.Direction.OUTPUT

# ── Stepper setup ─────────────────────────────────────────────────────────────
MOTOR_PIN_NAMES = [
    [board.GP0,  board.GP1,  board.GP2,  board.GP3],   # motor 1: inward
    [board.GP4,  board.GP5,  board.GP6,  board.GP7],   # motor 2: right curl tentacles 1&2
    [board.GP8,  board.GP9,  board.GP10, board.GP11],  # motor 3: right curl tentacles 3&4
    [board.GP12, board.GP13, board.GP14, board.GP15],  # motor 4: outward
]

MOTOR_MASKS = [
    0x000,   # motor 1 — no touch
    0x00C,   # electrodes 2 & 3 (bits 2,3) → motor 2 (tentacles 1&2)
    0x030,   # electrodes 4 & 5 (bits 4,5) → motor 3 (tentacles 3&4)
    0x000,   # motor 4 — no touch
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

SLOW_DELAY         = 0.003
FAST_DELAY         = 0.001
STEPS_PER_SWING    = 4096 * 3
STEPS_TOUCH_CURL   = int(STEPS_PER_SWING * 1.5)  # tighter curl: 1.5× normal swing

# ── Sequence phase state ──────────────────────────────────────────────────────
# phase_config[phase] = list of (motor_idx, direction) pairs active in that phase
phase_config = [
    [(0,  1)],          # phase 0: motor 1 forward  (all inward)
    [(3,  1)],          # phase 1: motor 4 forward  (all outward)
    [(1,  1)],          # phase 2: motor 2 forward  (tentacles 1&2 right)
    [(1, -1), (2, 1)],  # phase 3: motor 2 back + motor 3 forward (tentacles 3&4 right)
]

current_phase = 0
phase_done    = [False] * len(MOTOR_PIN_NAMES)

# ── Homing state (shared by both sequence homing and touch homing) ────────────
homing      = False
home_steps  = [0] * len(MOTOR_PIN_NAMES)
home_dirs   = [0] * len(MOTOR_PIN_NAMES)
home_reason = "sequence"  # "sequence" or "touch"

def start_phase(phase):
    global current_phase, phase_done
    current_phase = phase
    phase_done    = [False] * len(MOTOR_PIN_NAMES)
    for motor_idx, direction in phase_config[phase]:
        directions[motor_idx]  = direction
        step_counts[motor_idx] = 0
    print(f"→ Phase {phase}")

def start_homing(reason="sequence"):
    global homing, home_steps, home_dirs, home_reason
    homing      = True
    home_reason = reason
    for i in range(len(MOTOR_PIN_NAMES)):
        home_steps[i] = step_counts[i]                    # signed: retrace exact path
        home_dirs[i]  = -directions[i] if step_counts[i] != 0 else 0
        step_counts[i] = 0
    print(f"→ Homing ({reason})")

start_phase(0)

# ── Touch interrupt state ─────────────────────────────────────────────────────
# Only motors 2 and 3 (indices 1 and 2) respond to touch.
# Motors 1 and 4 (indices 0 and 3) are never touch-activated.
#
# Per-motor touch states:
#   TOUCH_IDLE     — not in a touch interaction
#   TOUCH_CURLING  — finger held, motor curling outward (tight swing)
#   TOUCH_HOMING   — finger released, motor returning to origin

TOUCH_IDLE    = 0
TOUCH_CURLING = 1
TOUCH_HOMING  = 2

touch_state = [TOUCH_IDLE] * len(MOTOR_PIN_NAMES)
touch_steps = [0]          * len(MOTOR_PIN_NAMES)  # steps taken during curl

# Global flag: sequence is interrupted by at least one active touch
touch_interrupted = False

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
led_state       = False
led_last_toggle = time.monotonic()
led_delay       = 0.25

# ── Main loop ─────────────────────────────────────────────────────────────────
print("Running — touch electrodes 2-3 → motor 2 tight curl | electrodes 4-5 → motor 3 | default: round-robin")

while True:
    now = time.monotonic()

    # ── LED + audio ───────────────────────────────────────────────────────────
    if now - led_last_toggle >= led_delay:
        led_state = not led_state
        led1.value = led_state
        led2.value = not led_state

        dist = get_distance()
        led_delay = distance_to_delay(dist)
        led_last_toggle = now
        print(f"dist={dist:.1f}cm  led_delay={led_delay:.3f}s")

        if dist < 999:
            set_tone(distance_to_midi(dist))
        else:
            set_tone(None)

    # ── Read touch sensor ─────────────────────────────────────────────────────
    status = mpr121_touched(i2c)

    # Only motors 1 and 2 (indices 1, 2) respond to touch; motors 0 and 3 never do.
    # MOTOR_MASKS[1] covers electrodes 2-3 (bits 2,3) → motor 2 (tentacles 1&2)
    # MOTOR_MASKS[2] covers electrodes 4-5 (bits 4,5) → motor 3 (tentacles 3&4)
    newly_interrupted = False
    for i in [1, 2]:
        touched = bool(status & MOTOR_MASKS[i])

        if touched:
            if touch_state[i] == TOUCH_IDLE:
                # First touch — if sequence is running, interrupt it
                if not touch_interrupted:
                    # Home all motors to cleanly exit the sequence
                    start_homing(reason="touch")
                touch_state[i]    = TOUCH_CURLING
                touch_steps[i]    = 0
                directions[i]     = 1          # outward curl direction
                newly_interrupted = True
                print(f"  Touch motor {i+1}: starting tight curl")

            elif touch_state[i] == TOUCH_HOMING:
                # Re-touched while returning — go forward again from current position
                touch_state[i] = TOUCH_CURLING
                directions[i]  = 1
                print(f"  Touch motor {i+1}: re-touched, curling again")

        else:
            if touch_state[i] == TOUCH_CURLING:
                # Finger lifted — return to origin
                touch_state[i] = TOUCH_HOMING
                directions[i]  = -1
                print(f"  Touch motor {i+1}: released, homing ({touch_steps[i]} steps)")

    if newly_interrupted:
        touch_interrupted = True

    # ── Motor movement ────────────────────────────────────────────────────────
    if touch_interrupted:
        # ── Touch interrupt mode ──────────────────────────────────────────────
        # Phase 1: home all motors from wherever the sequence left them
        if homing:
            all_home = True
            for i in range(len(MOTOR_PIN_NAMES)):
                if home_steps[i] != 0:
                    stepper_step(i, home_dirs[i], FAST_DELAY)
                    home_steps[i] -= 1
                    if home_steps[i] != 0:
                        all_home = False
            if all_home:
                homing = False
                print("  Sequence homed — touch curls now active")

        # Phase 2: run active touch curls (motors 1 and/or 2)
        if not homing:
            any_active = False
            for i in [1, 2]:
                if touch_state[i] == TOUCH_CURLING:
                    any_active = True
                    stepper_step(i, directions[i], FAST_DELAY)
                    touch_steps[i] += 1
                    step_counts[i]  = touch_steps[i]  # keep step_counts in sync for homing

                    if touch_steps[i] >= STEPS_TOUCH_CURL:
                        # Reached full tight curl — start returning even if still held
                        touch_state[i] = TOUCH_HOMING
                        directions[i]  = -1
                        print(f"  Touch motor {i+1}: full curl reached, returning")

                elif touch_state[i] == TOUCH_HOMING:
                    any_active = True
                    stepper_step(i, directions[i], FAST_DELAY)
                    touch_steps[i] -= 1
                    step_counts[i]  = touch_steps[i]

                    if touch_steps[i] <= 0:
                        touch_steps[i] = 0
                        step_counts[i] = 0
                        touch_state[i] = TOUCH_IDLE
                        print(f"  Touch motor {i+1}: homed")

            # All touch interactions complete — restart round-robin
            if not any_active and touch_state[1] == TOUCH_IDLE and touch_state[2] == TOUCH_IDLE:
                touch_interrupted = False
                start_phase(0)
                print("  All touches done → restarting sequence")

    else:
        # ── Normal round-robin sequence ───────────────────────────────────────
        if homing:
            all_home = True
            for i in range(len(MOTOR_PIN_NAMES)):
                if home_steps[i] != 0:
                    stepper_step(i, home_dirs[i], SLOW_DELAY)
                    home_steps[i] -= 1
                    if home_steps[i] != 0:
                        all_home = False
            if all_home:
                homing = False
                start_phase(0)

        else:
            active_motors = [m for m, d in phase_config[current_phase]]
            for i in active_motors:
                stepper_step(i, directions[i], SLOW_DELAY)
                step_counts[i] += 1
                if step_counts[i] >= STEPS_PER_SWING:
                    phase_done[i] = True

            if all(phase_done[i] for i in active_motors):
                next_phase = current_phase + 1
                if next_phase >= len(phase_config):
                    start_homing(reason="sequence")
                else:
                    start_phase(next_phase)