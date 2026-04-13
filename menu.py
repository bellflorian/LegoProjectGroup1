#!/usr/bin/env pybricks-micropython

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import ColorSensor
from pybricks.nxtdevices import LightSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait
import ujson

ev3 = EV3Brick()

# Sensors
left_sensor = LightSensor(Port.S4)      # left side on robot
right_sensor = ColorSensor(Port.S1)     # right side on robot

CALIBRATION_FILE = "calibration.json"


# -----------------------------
# Helper functions
# -----------------------------
def wait_for_button_release():
    while ev3.buttons.pressed():
        wait(20)


def wait_for_button_press():
    while True:
        pressed = ev3.buttons.pressed()
        if pressed:
            wait(120)
            return pressed
        wait(20)


def average(values):
    if len(values) == 0:
        return None
    return sum(values) / len(values)


def format_value(value):
    if value is None:
        return "-"
    return "{:.1f}".format(value)


def compute_threshold(black_values, white_values):
    black_avg = average(black_values)
    white_avg = average(white_values)

    if len(black_values) == 0 or len(white_values) == 0:
        return None, black_avg, white_avg

    black_max = max(black_values)

    # Threshold is intentionally closer to black because white can vary
    threshold = black_max + 0.35 * (white_avg - black_max)

    return threshold, black_avg, white_avg


def load_calibration():
    try:
        with open(CALIBRATION_FILE, "r") as f:
            return ujson.load(f)
    except:
        return {
            "left_sensor": {
                "sensor_type": "nxt_light_sensor",
                "black_samples": [],
                "white_samples": [],
                "black_avg": None,
                "white_avg": None,
                "threshold": None,
                "last_black": None,
                "last_white": None
            },
            "right_sensor": {
                "sensor_type": "ev3_color_sensor",
                "black_samples": [],
                "white_samples": [],
                "black_avg": None,
                "white_avg": None,
                "threshold": None,
                "last_black": None,
                "last_white": None
            }
        }


def save_calibration(data):
    with open(CALIBRATION_FILE, "w") as f:
        ujson.dump(data, f)


def ensure_sensor_keys(data, sensor_key):
    if "last_black" not in data[sensor_key]:
        data[sensor_key]["last_black"] = None
    if "last_white" not in data[sensor_key]:
        data[sensor_key]["last_white"] = None


def update_sensor_data(data, sensor_key, black_samples, white_samples, last_black, last_white):
    threshold, black_avg, white_avg = compute_threshold(black_samples, white_samples)

    data[sensor_key]["black_samples"] = black_samples
    data[sensor_key]["white_samples"] = white_samples
    data[sensor_key]["black_avg"] = black_avg
    data[sensor_key]["white_avg"] = white_avg
    data[sensor_key]["threshold"] = threshold
    data[sensor_key]["last_black"] = last_black
    data[sensor_key]["last_white"] = last_white

    save_calibration(data)


def read_sensor_value(sensor):
    return sensor.reflection()


# -----------------------------
# Screen drawing
# -----------------------------
def draw_menu(title, items, selected):
    ev3.screen.clear()
    ev3.screen.draw_text(0, 0, title)

    y = 20
    for i, item in enumerate(items):
        prefix = ">" if i == selected else " "
        ev3.screen.draw_text(0, y, prefix + " " + item)
        y += 20


def draw_calibration_screen(sensor_name, last_black, avg_black, last_white, avg_white):
    ev3.screen.clear()

    ev3.screen.draw_text(0, 0, sensor_name)

    ev3.screen.draw_text(0, 20, "Black")
    ev3.screen.draw_text(0, 35, "Last: {}".format(format_value(last_black)))
    ev3.screen.draw_text(0, 50, "Avg : {}".format(format_value(avg_black)))

    ev3.screen.draw_text(0, 72, "White")
    ev3.screen.draw_text(0, 87, "Last: {}".format(format_value(last_white)))
    ev3.screen.draw_text(0, 102, "Avg : {}".format(format_value(avg_white)))


def draw_values_screen(data):
    left_thr = data["left_sensor"]["threshold"]
    right_thr = data["right_sensor"]["threshold"]

    ev3.screen.clear()
    ev3.screen.draw_text(0, 0, "Saved values")
    ev3.screen.draw_text(0, 25, "Left  T: {}".format(format_value(left_thr)))
    ev3.screen.draw_text(0, 50, "Right T: {}".format(format_value(right_thr)))
    ev3.screen.draw_text(0, 95, "CENTER/LEFT back")


def draw_live_values_screen(left_value, right_value):
    ev3.screen.clear()
    ev3.screen.draw_text(0, 0, "Live values")
    ev3.screen.draw_text(0, 30, "Left : {}".format(left_value))
    ev3.screen.draw_text(0, 55, "Right: {}".format(right_value))
    ev3.screen.draw_text(0, 95, "CENTER/LEFT back")


# -----------------------------
# Calibration
# -----------------------------
def calibrate_sensor(sensor, sensor_key, sensor_name):
    data = load_calibration()
    ensure_sensor_keys(data, sensor_key)

    black_samples = list(data[sensor_key]["black_samples"])
    white_samples = list(data[sensor_key]["white_samples"])
    last_black = data[sensor_key]["last_black"]
    last_white = data[sensor_key]["last_white"]

    while True:
        avg_black = average(black_samples)
        avg_white = average(white_samples)

        draw_calibration_screen(sensor_name, last_black, avg_black, last_white, avg_white)

        pressed = wait_for_button_press()

        # LEFT   -> store black
        # RIGHT  -> store white
        # DOWN   -> clear samples
        # CENTER -> back

        if Button.LEFT in pressed:
            value = read_sensor_value(sensor)
            black_samples.append(value)
            last_black = value
            update_sensor_data(
                data, sensor_key,
                black_samples, white_samples,
                last_black, last_white
            )
            ev3.speaker.beep()
            wait_for_button_release()

        elif Button.RIGHT in pressed:
            value = read_sensor_value(sensor)
            white_samples.append(value)
            last_white = value
            update_sensor_data(
                data, sensor_key,
                black_samples, white_samples,
                last_black, last_white
            )
            ev3.speaker.beep()
            wait_for_button_release()

        elif Button.DOWN in pressed:
            black_samples = []
            white_samples = []
            last_black = None
            last_white = None
            update_sensor_data(
                data, sensor_key,
                black_samples, white_samples,
                last_black, last_white
            )
            ev3.speaker.beep()
            wait_for_button_release()

        elif Button.CENTER in pressed:
            wait_for_button_release()
            return


def sensor_selection_menu():
    items = ["Left sensor", "Right sensor", "Back"]
    selected = 0

    while True:
        draw_menu("Select sensor", items, selected)
        pressed = wait_for_button_press()

        if Button.UP in pressed:
            selected = (selected - 1) % len(items)
            wait_for_button_release()

        elif Button.DOWN in pressed:
            selected = (selected + 1) % len(items)
            wait_for_button_release()

        elif Button.CENTER in pressed:
            wait_for_button_release()

            if selected == 0:
                calibrate_sensor(left_sensor, "left_sensor", "Left sensor")
            elif selected == 1:
                calibrate_sensor(right_sensor, "right_sensor", "Right sensor")
            elif selected == 2:
                return

        elif Button.LEFT in pressed:
            wait_for_button_release()
            return


def show_saved_values():
    while True:
        data = load_calibration()
        draw_values_screen(data)

        pressed = wait_for_button_press()
        if Button.CENTER in pressed or Button.LEFT in pressed:
            wait_for_button_release()
            return


def show_live_values():
    while True:
        left_value = read_sensor_value(left_sensor)
        right_value = read_sensor_value(right_sensor)

        draw_live_values_screen(left_value, right_value)

        pressed = ev3.buttons.pressed()
        if Button.CENTER in pressed or Button.LEFT in pressed:
            wait_for_button_release()
            return

        wait(100)


def start_placeholder():
    ev3.screen.clear()
    ev3.screen.draw_text(0, 40, "Start not ready")
    wait(1000)


# -----------------------------
# Main menu
# -----------------------------
def main_menu():
    items = ["Calibrate", "Show values", "Live values", "Start"]
    selected = 0

    while True:
        draw_menu("Main menu", items, selected)
        pressed = wait_for_button_press()

        if Button.UP in pressed:
            selected = (selected - 1) % len(items)
            wait_for_button_release()

        elif Button.DOWN in pressed:
            selected = (selected + 1) % len(items)
            wait_for_button_release()

        elif Button.CENTER in pressed:
            wait_for_button_release()

            if selected == 0:
                sensor_selection_menu()
            elif selected == 1:
                show_saved_values()
            elif selected == 2:
                show_live_values()
            elif selected == 3:
                start_placeholder()


# -----------------------------
# Program start
# -----------------------------
ev3.screen.clear()
ev3.screen.draw_text(0, 40, "Starting menu...")
wait(800)
main_menu()