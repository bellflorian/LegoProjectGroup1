#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.nxtdevices import LightSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait

# =========================================================
# HARDWARE SETUP
# =========================================================
ev3 = EV3Brick()

left_motor = Motor(Port.A)
right_motor = Motor(Port.D)

right_sensor = ColorSensor(Port.S1)
left_sensor = LightSensor(Port.S4)

# =========================================================
# GLOBAL TUNING PARAMETERS
# =========================================================

BASE_SPEED_SCALE = 1.00  
# Global multiplier for ALL speeds → increase = everything faster, decrease = everything slower

FORWARD_SPEED = 500  
# Speed while driving straight forward (main movement)

REVERSE_SPEED = 260  
# Speed used when driving backwards after detecting a line

REVERSE_TIME_MS = 560  
# How long the robot drives backwards (normal correction)

SHARP_REVERSE_TIME_MS = 760  
# Longer backward movement for sharp curves (when normal correction wasn't enough)

TURN_SPEED = 280  
# Speed used while turning (left/right rotation)

TURN_TIME_MS = 320  
# Duration of a normal turn after detecting a line

SHARP_TURN_TIME_MS = 420  
# Longer turn for sharp curves (more aggressive correction)

EXIT_FORWARD_SPEED = 260  
# Speed when moving forward briefly after a correction

EXIT_FORWARD_TIME_MS = 120  
# Short forward movement after turning to stabilize direction

LEFT_BLACK_THRESHOLD = 48  
# Sensor value threshold → if left sensor is BELOW this, it detects black

RIGHT_BLACK_THRESHOLD = 15  
# Same as above, but for right sensor (different because sensors behave differently)

SHARP_CURVE_WINDOW_MS = 800  
# Time window: if another line is detected within this time → treat it as a sharp curve

DETECTION_COOLDOWN_MS = 140  
# Pause after a correction → prevents reacting multiple times to the same line

LOOP_DELAY_MS = 10  
# Delay of the main loop → controls how often sensors are checked (lower = more responsive)

# =========================================================
# STATE
# =========================================================

time_since_last_correction_ms = 999999

# =========================================================
# CONFIG MENU
# =========================================================

CONFIG_ITEMS = [
    ("BASE_SPEED_SCALE", "float", 0.05, 0.10, 3.00),
    ("FORWARD_SPEED", "int", 10, 50, 1200),
    ("REVERSE_SPEED", "int", 10, 50, 1200),
    ("REVERSE_TIME_MS", "int", 10, 0, 3000),
    ("SHARP_REVERSE_TIME_MS", "int", 10, 0, 3000),
    ("TURN_SPEED", "int", 10, 50, 1200),
    ("TURN_TIME_MS", "int", 10, 0, 3000),
    ("SHARP_TURN_TIME_MS", "int", 10, 0, 3000),
    ("EXIT_FORWARD_SPEED", "int", 10, 0, 1200),
    ("EXIT_FORWARD_TIME_MS", "int", 10, 0, 3000),
    ("LEFT_BLACK_THRESHOLD", "int", 1, 0, 100),
    ("RIGHT_BLACK_THRESHOLD", "int", 1, 0, 100),
    ("SHARP_CURVE_WINDOW_MS", "int", 10, 0, 5000),
    ("DETECTION_COOLDOWN_MS", "int", 10, 0, 5000),
    ("LOOP_DELAY_MS", "int", 1, 1, 1000),
]

# =========================================================
# HELPERS
# =========================================================

def scale(value):
    return int(value * BASE_SPEED_SCALE)

def left_black():
    return left_sensor.reflection() <= LEFT_BLACK_THRESHOLD

def right_black():
    return right_sensor.reflection() <= RIGHT_BLACK_THRESHOLD

def any_button_pressed():
    return len(ev3.buttons.pressed()) > 0

def stop_robot():
    left_motor.stop()
    right_motor.stop()

def drive_forward():
    left_motor.run(scale(FORWARD_SPEED))
    right_motor.run(scale(FORWARD_SPEED))

def wait_release():
    while ev3.buttons.pressed():
        wait(20)

def adjust(name, value_type, step, min_value, max_value, direction):
    value = globals()[name]
    value += step * direction
    value = max(min_value, min(max_value, value))

    if value_type == "float":
        globals()[name] = round(value, 2)
    else:
        globals()[name] = int(value)

def sharp_curve():
    return time_since_last_correction_ms < SHARP_CURVE_WINDOW_MS

def mark_done():
    global time_since_last_correction_ms
    time_since_last_correction_ms = 0

# =========================================================
# CANCELLABLE WAIT / MOTION
# =========================================================

def safe_wait(ms):
    global time_since_last_correction_ms

    elapsed = 0
    while elapsed < ms:
        if any_button_pressed():
            stop_robot()
            return False
        wait(10)
        elapsed += 10
        time_since_last_correction_ms += 10
    return True

def backward(ms):
    left_motor.run(-scale(REVERSE_SPEED))
    right_motor.run(-scale(REVERSE_SPEED))
    ok = safe_wait(ms)
    stop_robot()
    return ok

def turn_left(ms):
    left_motor.run(-scale(TURN_SPEED))
    right_motor.run(scale(TURN_SPEED))
    ok = safe_wait(ms)
    stop_robot()
    return ok

def turn_right(ms):
    left_motor.run(scale(TURN_SPEED))
    right_motor.run(-scale(TURN_SPEED))
    ok = safe_wait(ms)
    stop_robot()
    return ok

def exit_forward(ms):
    left_motor.run(scale(EXIT_FORWARD_SPEED))
    right_motor.run(scale(EXIT_FORWARD_SPEED))
    ok = safe_wait(ms)
    stop_robot()
    return ok

# =========================================================
# DISPLAY
# =========================================================

def draw_main_menu(index):
    entries = ["START", "CONFIG"]

    ev3.screen.clear()
    ev3.screen.draw_text(10, 10, "MAIN MENU")

    for i, entry in enumerate(entries):
        prefix = ">" if i == index else " "
        ev3.screen.draw_text(10, 30 + i * 20, prefix + " " + entry)

def draw_config(index, start):
    ev3.screen.clear()
    ev3.screen.draw_text(0, 0, "CONFIG")

    visible = 3
    row_height = 40

    for i in range(visible):
        j = start + i
        if j >= len(CONFIG_ITEMS):
            break

        name = CONFIG_ITEMS[j][0]
        prefix = ">" if j == index else " "
        y = 15 + i * row_height

        ev3.screen.draw_text(0, y, prefix + name)
        ev3.screen.draw_text(10, y + 15, str(globals()[name]))

def draw_angry_face():
    ev3.screen.clear()

    # ===== EYEBROWS =====
    for i in range(6):
        ev3.screen.draw_line(20, 25 + i, 80, 15 + i)     # links
        ev3.screen.draw_line(160, 25 + i, 100, 15 + i)   # rechts

    # ===== LEFT EYE (Box) =====
    for y in range(40, 65):
        ev3.screen.draw_line(30, y, 80, y)

    # ===== RIGHT EYE (Box) =====
    for y in range(40, 65):
        ev3.screen.draw_line(100, y, 150, y)

    # ===== PUPILS =====
    for y in range(48, 58):
        ev3.screen.draw_line(50, y, 60, y)
        ev3.screen.draw_line(120, y, 130, y)

    # ===== ZICKZACK MOUTH =====
    # dicke Linien für aggressiven Look
    for i in range(6):
        ev3.screen.draw_line(30, 100 + i, 60, 90 + i)
        ev3.screen.draw_line(60, 90 + i, 90, 100 + i)
        ev3.screen.draw_line(90, 100 + i, 120, 90 + i)
        ev3.screen.draw_line(120, 90 + i, 150, 100 + i)

# =========================================================
# MENUS
# =========================================================

def main_menu():
    index = 0
    entries = ["START", "CONFIG"]

    while True:
        draw_main_menu(index)
        pressed = ev3.buttons.pressed()

        if Button.UP in pressed:
            index = (index - 1) % len(entries)
            wait_release()

        elif Button.DOWN in pressed:
            index = (index + 1) % len(entries)
            wait_release()

        elif Button.CENTER in pressed:
            wait_release()
            return entries[index]

        wait(100)

def config_menu():
    index = 0

    while True:
        start = max(0, index - 2)
        draw_config(index, start)

        pressed = ev3.buttons.pressed()

        if Button.UP in pressed:
            index = (index - 1) % len(CONFIG_ITEMS)
            wait_release()

        elif Button.DOWN in pressed:
            index = (index + 1) % len(CONFIG_ITEMS)
            wait_release()

        elif Button.LEFT in pressed:
            name, value_type, step, min_value, max_value = CONFIG_ITEMS[index]
            adjust(name, value_type, step, min_value, max_value, -1)
            wait_release()

        elif Button.RIGHT in pressed:
            name, value_type, step, min_value, max_value = CONFIG_ITEMS[index]
            adjust(name, value_type, step, min_value, max_value, 1)
            wait_release()

        elif Button.CENTER in pressed:
            wait_release()
            return

        wait(100)

# =========================================================
# DRIVE LOGIC
# =========================================================

def handle_right_line():
    if not safe_wait(50):
        return False

    if sharp_curve():
        if not backward(SHARP_REVERSE_TIME_MS):
            return False
        if not turn_left(SHARP_TURN_TIME_MS):
            return False
    else:
        if not backward(REVERSE_TIME_MS):
            return False
        if not turn_left(TURN_TIME_MS):
            return False

    if not exit_forward(EXIT_FORWARD_TIME_MS):
        return False

    mark_done()

    if not safe_wait(DETECTION_COOLDOWN_MS):
        return False

    return True

def handle_left_line():
    if not safe_wait(50):
        return False

    if sharp_curve():
        if not backward(SHARP_REVERSE_TIME_MS):
            return False
        if not turn_right(SHARP_TURN_TIME_MS):
            return False
    else:
        if not backward(REVERSE_TIME_MS):
            return False
        if not turn_right(TURN_TIME_MS):
            return False

    if not exit_forward(EXIT_FORWARD_TIME_MS):
        return False

    mark_done()

    if not safe_wait(DETECTION_COOLDOWN_MS):
        return False

    return True

def drive():
    global time_since_last_correction_ms
    time_since_last_correction_ms = 999999

    draw_angry_face()

    while True:
        if any_button_pressed():
            stop_robot()
            wait_release()
            return

        drive_forward()

        if right_black():
            stop_robot()
            if not handle_right_line():
                wait_release()
                return

        elif left_black():
            stop_robot()
            if not handle_left_line():
                wait_release()
                return

        wait(LOOP_DELAY_MS)
        time_since_last_correction_ms += LOOP_DELAY_MS

# =========================================================
# MAIN LOOP
# =========================================================

while True:
    action = main_menu()

    if action == "START":
        drive()

    elif action == "CONFIG":
        config_menu()