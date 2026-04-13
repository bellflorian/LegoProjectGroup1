#!/usr/bin/env pybricks-micropython

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.nxtdevices import LightSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait
from pybricks.robotics import DriveBase
import ujson

ev3 = EV3Brick()

# Motors
left_motor = Motor(Port.A)
right_motor = Motor(Port.D)

# Sensors
left_sensor = LightSensor(Port.S4)
right_sensor = ColorSensor(Port.S1)

# Robot
robot = DriveBase(left_motor, right_motor, wheel_diameter=40, axle_track=70)

CALIBRATION_FILE = "calibration.json"

# ----------------------------------------
# Tuning parameters
# ----------------------------------------
BASE_SPEED_FAST = 200
BASE_SPEED_MEDIUM = 100
BASE_SPEED_SLOW = 50

DEADZONE = 2.0

SMALL_GAIN = 8
MEDIUM_GAIN = 16
HARD_GAIN = 28

MAX_TURN_RATE = 500

LOOP_DELAY = 10


# ----------------------------------------
# File loading
# ----------------------------------------
def load_calibration():
    try:
        with open(CALIBRATION_FILE, "r") as f:
            return ujson.load(f)
    except:
        return None


# ----------------------------------------
# Helpers
# ----------------------------------------
def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def show_message(line1="", line2="", line3="", line4=""):
    ev3.screen.clear()
    if line1:
        ev3.screen.draw_text(0, 0, line1)
    if line2:
        ev3.screen.draw_text(0, 18, line2)
    if line3:
        ev3.screen.draw_text(0, 36, line3)
    if line4:
        ev3.screen.draw_text(0, 54, line4)


def show_idle_screen():
    ev3.screen.clear()
    ev3.screen.draw_text(0, 0, "Line follower")
    ev3.screen.draw_text(0, 20, "LEFT  = left sensor")
    ev3.screen.draw_text(0, 38, "RIGHT = right sensor")
    ev3.screen.draw_text(0, 56, "CENTER stops run")


def get_sensor_setup(data, sensor_key):
    black_avg = data[sensor_key]["black_avg"]
    white_avg = data[sensor_key]["white_avg"]

    if black_avg is None or white_avg is None:
        return None

    target = (black_avg + white_avg) / 2

    return {
        "black_avg": black_avg,
        "white_avg": white_avg,
        "target": target
    }


def read_left():
    return left_sensor.reflection()


def read_right():
    return right_sensor.reflection()


# ----------------------------------------
# Dynamic line follower
# ----------------------------------------
def compute_turn_and_speed(error):
    abs_error = abs(error)

    # Deadzone for smoother straight sections
    if abs_error < DEADZONE:
        return BASE_SPEED_FAST, 0, "STRAIGHT"

    # Small correction
    if abs_error < 5:
        turn_rate = int(error * SMALL_GAIN)
        turn_rate = clamp(turn_rate, -MAX_TURN_RATE, MAX_TURN_RATE)
        return BASE_SPEED_FAST, turn_rate, "LIGHT CURVE"

    # Medium correction
    if abs_error < 10:
        turn_rate = int(error * MEDIUM_GAIN)
        turn_rate = clamp(turn_rate, -MAX_TURN_RATE, MAX_TURN_RATE)
        return BASE_SPEED_MEDIUM, turn_rate, "CURVE"

    # Hard correction
    turn_rate = int(error * HARD_GAIN)
    turn_rate = clamp(turn_rate, -MAX_TURN_RATE, MAX_TURN_RATE)
    return BASE_SPEED_SLOW, turn_rate, "HARD CURVE"


def run_line_follower(sensor_name, read_sensor, sensor_setup, invert_turn=False):
    target = sensor_setup["target"]

    while True:
        value = read_sensor()
        error = value - target

        if invert_turn:
            error = -error

        speed, turn_rate, state = compute_turn_and_speed(error)

        robot.drive(speed, turn_rate)

        ev3.screen.clear()
        ev3.screen.draw_text(0, 0, sensor_name)
        ev3.screen.draw_text(0, 18, state)
        ev3.screen.draw_text(0, 36, "Val: {:>4}".format(value))
        ev3.screen.draw_text(0, 54, "Tar: {:>4.1f}".format(target))
        ev3.screen.draw_text(0, 72, "Err: {:>4.1f}".format(error))
        ev3.screen.draw_text(0, 90, "S:{} T:{}".format(speed, turn_rate))

        if Button.CENTER in ev3.buttons.pressed():
            robot.stop()
            while ev3.buttons.pressed():
                wait(20)
            return

        wait(LOOP_DELAY)


# ----------------------------------------
# Main
# ----------------------------------------
data = load_calibration()

if data is None:
    show_message("No calibration file", "Run menu first")
    wait(2000)
    raise SystemExit

left_setup = get_sensor_setup(data, "left_sensor")
right_setup = get_sensor_setup(data, "right_sensor")

if left_setup is None or right_setup is None:
    show_message("Calibration missing", "Run menu first")
    wait(2000)
    raise SystemExit

while True:
    show_idle_screen()
    pressed = ev3.buttons.pressed()

    if Button.LEFT in pressed:
        while ev3.buttons.pressed():
            wait(20)
        run_line_follower("Left sensor", read_left, left_setup, invert_turn=False)

    elif Button.RIGHT in pressed:
        while ev3.buttons.pressed():
            wait(20)
        run_line_follower("Right sensor", read_right, right_setup, invert_turn=False)

    wait(20)