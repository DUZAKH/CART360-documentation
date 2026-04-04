# Modified stepper motor code with MPR121 touch sensor
# MPR121 triggers fast back-and-forth on pins 0-2 touch
# Default: slow back-and-forth when nothing touched

from machine import Pin, I2C
from time import sleep

# ── MPR121 ──────────────────────────────────────────────────────────────────
MPR121_ADDR = 0x5A

def mpr121_init(i2c):
    i2c.writeto_mem(MPR121_ADDR, 0x80, bytes([0x63]))  # soft reset
    sleep(0.001)
    i2c.writeto_mem(MPR121_ADDR, 0x5E, bytes([0x00]))  # stop mode
    # touch/release thresholds for electrodes 0-2
    for ch in range(3):
        i2c.writeto_mem(MPR121_ADDR, 0x41 + ch * 2, bytes([12]))  # touch
        i2c.writeto_mem(MPR121_ADDR, 0x42 + ch * 2, bytes([6]))   # release
    # baseline filter & config registers
    i2c.writeto_mem(MPR121_ADDR, 0x2B, bytes([0x01]))
    i2c.writeto_mem(MPR121_ADDR, 0x2C, bytes([0x01]))
    i2c.writeto_mem(MPR121_ADDR, 0x2D, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x2E, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x2F, bytes([0x01]))
    i2c.writeto_mem(MPR121_ADDR, 0x30, bytes([0x01]))
    i2c.writeto_mem(MPR121_ADDR, 0x31, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x32, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x33, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x34, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x35, bytes([0x00]))
    i2c.writeto_mem(MPR121_ADDR, 0x5C, bytes([0x10]))  # AFE config
    i2c.writeto_mem(MPR121_ADDR, 0x5D, bytes([0x24]))  # filter config
    i2c.writeto_mem(MPR121_ADDR, 0x5E, bytes([0x0C]))  # enable 12 electrodes

def mpr121_touched(i2c):
    """Returns a 12-bit integer; bit N = electrode N is touched."""
    data = i2c.readfrom_mem(MPR121_ADDR, 0x00, 2)
    return (data[1] << 8) | data[0]

def pins_0_2_touched(i2c):
    """True if any of electrodes 0, 1, or 2 are currently touched."""
    status = mpr121_touched(i2c)
    return bool(status & 0x07)  # 0b00000111 masks pins 0, 1, 2

# ── Stepper setup ────────────────────────────────────────────────────────────
motor_GP = [0, 1, 2, 3]          # adjust to your wiring (moved off 0-3 to free I2C-friendly pins)
seq_pointer = [0, 1, 2, 3, 4, 5, 6, 7]

stepper_obj = [Pin(gp, Pin.OUT) for gp in motor_GP]

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

# ── Timing & motion config ───────────────────────────────────────────────────
SLOW_DELAY      = 0.005   # seconds per step when idle
FAST_DELAY      = 0.001   # smaller = faster
STEPS_PER_SWING = 4096     # steps in one direction before reversing

# ── I2C init ─────────────────────────────────────────────────────────────────
# SDA = GP20, SCL = GP21 — change to match your wiring
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=400_000)
print("I2C devices found:", [hex(a) for a in i2c.scan()])
mpr121_init(i2c)
print("MPR121 ready.")

# ── Stepper helpers ───────────────────────────────────────────────────────────
def stepper_step(direction, delay):
    """Advance one step in the given direction (+1 or -1) then sleep."""
    global seq_pointer
    seq_pointer = seq_pointer[direction:] + seq_pointer[:direction]
    for a in range(4):
        stepper_obj[a].value(arrSeq[seq_pointer[0]][a])
    sleep(delay)

def stepper_off():
    """De-energise all coils to reduce heat when paused."""
    for pin in stepper_obj:
        pin.value(0)

# ── Main loop ─────────────────────────────────────────────────────────────────
print("Running — touch electrodes 0-2 to speed up.")

direction   = 1    # +1 or -1
step_count  = 0

while True:
    touched = pins_0_2_touched(i2c)
    delay   = FAST_DELAY if touched else SLOW_DELAY

    stepper_step(direction, delay)
    step_count += 1

    if step_count >= STEPS_PER_SWING:
        step_count = 0
        direction  = -direction   # reverse