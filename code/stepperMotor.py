# Modified stepper motor code with MPR121 touch sensor
# MPR121 pins 0-2 → motor 1 fast
# MPR121 pins 3-5 → motor 2 fast
# MPR121 pins 6-8 → motor 3 fast
# nothing touched → all slow

from machine import Pin, I2C
from time import sleep

# ── MPR121 ──────────────────────────────────────────────────────────────────
MPR121_ADDR = 0x5A

def mpr121_init(i2c):
    i2c.writeto_mem(MPR121_ADDR, 0x80, bytes([0x63]))  # soft reset
    sleep(0.001)
    i2c.writeto_mem(MPR121_ADDR, 0x5E, bytes([0x00]))  # stop mode
    for ch in range(9):                                 # electrodes 0-8
        i2c.writeto_mem(MPR121_ADDR, 0x41 + ch * 2, bytes([12]))
        i2c.writeto_mem(MPR121_ADDR, 0x42 + ch * 2, bytes([6]))
    i2c.writeto_mem(MPR121_ADDR, 0x5C, bytes([0x10]))
    i2c.writeto_mem(MPR121_ADDR, 0x5D, bytes([0x24]))
    i2c.writeto_mem(MPR121_ADDR, 0x5E, bytes([0x0C]))

def mpr121_touched(i2c):
    data = i2c.readfrom_mem(MPR121_ADDR, 0x00, 2)
    return (data[1] << 8) | data[0]

# ── Stepper setup ────────────────────────────────────────────────────────────
MOTOR_PINS = [
    [0,  1,  2,  3],
    [4,  5,  6,  7],
    [8,  9, 10, 11],
]

# one mask per motor — which MPR121 electrodes control it
MOTOR_MASKS = [
    0x007,   # 0b000001111  electrodes 0-2
    0x038,   # 0b000111000  electrodes 3-5
    0x1C0,   # 0b111000000  electrodes 6-8
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

stepper_pins = [[Pin(gp, Pin.OUT) for gp in pins] for pins in MOTOR_PINS]
seq_pointers = [[0,1,2,3,4,5,6,7]] * len(MOTOR_PINS)
directions   = [1]  * len(MOTOR_PINS)
step_counts  = [0]  * len(MOTOR_PINS)

# ── Timing & motion config ───────────────────────────────────────────────────
SLOW_DELAY      = 0.005
FAST_DELAY      = 0.001
STEPS_PER_SWING = 4096

# ── I2C init ─────────────────────────────────────────────────────────────────
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=400_000)
mpr121_init(i2c)

# ── Stepper helpers ───────────────────────────────────────────────────────────
def stepper_step(motor_idx, direction, delay):
    seq_pointers[motor_idx] = (
        seq_pointers[motor_idx][direction:] +
        seq_pointers[motor_idx][:direction]
    )
    for a in range(4):
        stepper_pins[motor_idx][a].value(arrSeq[seq_pointers[motor_idx][0]][a])
    sleep(delay)

def stepper_off(motor_idx):
    for pin in stepper_pins[motor_idx]:
        pin.value(0)

# ── Main loop ─────────────────────────────────────────────────────────────────
print("Running — pins 0-2 → motor 1, pins 3-5 → motor 2, pins 6-8 → motor 3")

while True:
    status = mpr121_touched(i2c)

    for i in range(len(MOTOR_PINS)):
        delay = FAST_DELAY if (status & MOTOR_MASKS[i]) else SLOW_DELAY
        stepper_step(i, directions[i], delay)
        step_counts[i] += 1
        if step_counts[i] >= STEPS_PER_SWING:
            step_counts[i] = 0
            directions[i] = -directions[i]