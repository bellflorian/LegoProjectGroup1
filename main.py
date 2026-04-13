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

LEFT_MOTOR_PORT = Port.A
RIGHT_MOTOR_PORT = Port.D

RIGHT_SENSOR_PORT = Port.S1   # EV3 Color Sensor
LEFT_SENSOR_PORT = Port.S4    # NXT Light Sensor

left_motor = Motor(LEFT_MOTOR_PORT)
right_motor = Motor(RIGHT_MOTOR_PORT)

right_sensor = ColorSensor(RIGHT_SENSOR_PORT)
left_sensor = LightSensor(LEFT_SENSOR_PORT)

# =========================================================
# GLOBAL TUNING PARAMETERS
# =========================================================

# Master scaling for all motor speeds
BASE_SPEED_SCALE = 1.00

FORWARD_SPEED = 500

REVERSE_SPEED = 260
REVERSE_TIME_MS = 560
SHARP_REVERSE_TIME_MS = 760

TURN_SPEED = 280
TURN_TIME_MS = 320
SHARP_TURN_TIME_MS = 420

EXIT_FORWARD_SPEED = 260
EXIT_FORWARD_TIME_MS = 120

DETECTION_COOLDOWN_MS = 140
SHARP_CURVE_WINDOW_MS = 800

# Sensor thresholds
LEFT_BLACK_THRESHOLD = 48
RIGHT_BLACK_THRESHOLD = 15

# Main loop delay
LOOP_DELAY_MS = 10

# =========================================================
# STATE
# =========================================================

time_since_last_correction_ms = 999999

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def scale(value):
    return int(value * BASE_SPEED_SCALE)

def get_left_value():
    return left_sensor.reflection()

def get_right_value():
    return right_sensor.reflection()

def left_detects_black():
    return get_left_value() <= LEFT_BLACK_THRESHOLD

def right_detects_black():
    return get_right_value() <= RIGHT_BLACK_THRESHOLD

def stop_robot():
    left_motor.stop()
    right_motor.stop()

def drive_forward():
    left_motor.run(scale(FORWARD_SPEED))
    right_motor.run(scale(FORWARD_SPEED))

def drive_backward(duration_ms):
    left_motor.run(-scale(REVERSE_SPEED))
    right_motor.run(-scale(REVERSE_SPEED))
    safe_wait(duration_ms)
    stop_robot()

def turn_left(duration_ms):
    left_motor.run(-scale(TURN_SPEED))
    right_motor.run(scale(TURN_SPEED))
    safe_wait(duration_ms)
    stop_robot()

def turn_right(duration_ms):
    left_motor.run(scale(TURN_SPEED))
    right_motor.run(-scale(TURN_SPEED))
    safe_wait(duration_ms)
    stop_robot()

def exit_forward(duration_ms):
    if duration_ms > 0:
        left_motor.run(scale(EXIT_FORWARD_SPEED))
        right_motor.run(scale(EXIT_FORWARD_SPEED))
        safe_wait(duration_ms)
        stop_robot()

def center_pressed():
    return Button.CENTER in ev3.buttons.pressed()

def safe_wait(duration_ms):
    global time_since_last_correction_ms

    elapsed = 0
    step = 10

    while elapsed < duration_ms:
        if center_pressed():
            stop_robot()
            ev3.speaker.beep()
            raise SystemExit

        wait(step)
        elapsed += step
        time_since_last_correction_ms += step

def is_sharp_curve():
    return time_since_last_correction_ms <= SHARP_CURVE_WINDOW_MS

def mark_correction_done():
    global time_since_last_correction_ms
    time_since_last_correction_ms = 0

# =========================================================
# REACTION LOGIC
# =========================================================

def handle_right_line():
    """
    Right sensor detects black:
    stop -> reverse -> turn left -> short forward -> continue
    Uses a stronger correction if this happens shortly after
    the previous correction.
    """
    sharp_curve = is_sharp_curve()

    stop_robot()
    safe_wait(60)

    if sharp_curve:
        drive_backward(SHARP_REVERSE_TIME_MS)
        safe_wait(40)
        turn_left(SHARP_TURN_TIME_MS)
    else:
        drive_backward(REVERSE_TIME_MS)
        safe_wait(40)
        turn_left(TURN_TIME_MS)

    safe_wait(40)
    exit_forward(EXIT_FORWARD_TIME_MS)
    mark_correction_done()

def handle_left_line():
    """
    Left sensor detects black:
    stop -> reverse -> turn right -> short forward -> continue
    Uses a stronger correction if this happens shortly after
    the previous correction.
    """
    sharp_curve = is_sharp_curve()

    stop_robot()
    safe_wait(60)

    if sharp_curve:
        drive_backward(SHARP_REVERSE_TIME_MS)
        safe_wait(40)
        turn_right(SHARP_TURN_TIME_MS)
    else:
        drive_backward(REVERSE_TIME_MS)
        safe_wait(40)
        turn_right(TURN_TIME_MS)

    safe_wait(40)
    exit_forward(EXIT_FORWARD_TIME_MS)
    mark_correction_done()

# =========================================================
# START CONTROL
# =========================================================

def wait_for_start():
    ev3.screen.clear()
    ev3.screen.draw_text(10, 20, "LEFT = Start")
    ev3.screen.draw_text(10, 40, "CENTER = Stop")
    ev3.speaker.beep()

    while True:
        if Button.LEFT in ev3.buttons.pressed():
            wait(250)
            ev3.speaker.beep()
            return
        wait(20)

# =========================================================
# MAIN LOOP
# =========================================================

wait_for_start()

try:
    while True:
        if center_pressed():
            stop_robot()
            ev3.speaker.beep()
            break

        drive_forward()

        if right_detects_black():
            handle_right_line()
            safe_wait(DETECTION_COOLDOWN_MS)

        elif left_detects_black():
            handle_left_line()
            safe_wait(DETECTION_COOLDOWN_MS)

        wait(LOOP_DELAY_MS)
        time_since_last_correction_ms += LOOP_DELAY_MS

except SystemExit:
    stop_robot()