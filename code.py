# ---------- VARIABLES -------------#
last_poll_ts = -1000

# ---------- IMPORT REQUIRED TO SHOW SPLASH -------------#
from board import I2C, BUTTON, D1, D2, DISPLAY
from debug import debug
from settings import MQTT_POLL_FREQ, BRIGHTNESS_OPTIONS, BRIGHTNESS_INITIAL_INDEX
from adxl343 import Accelerometer
from orientation import Orientation, ORIENTATION_RIGHT, ORIENTATION_LEFT, ORIENTATION_STANDING, ORIENTATION_UPSIDE_DOWN, ORIENTATION_FACE_DOWN, ORIENTATION_FACE_UP
from gui import Gui

# ---------- DISPLAY SETUP -------------#
debug('Initializing display')
current_brightness_index = BRIGHTNESS_INITIAL_INDEX
DISPLAY.brightness = BRIGHTNESS_OPTIONS[BRIGHTNESS_INITIAL_INDEX]
DISPLAY.auto_refresh = False

def change_brightness():
    global current_brightness_index
    current_brightness_index = (current_brightness_index + 1) % len(BRIGHTNESS_OPTIONS)
    DISPLAY.brightness = BRIGHTNESS_OPTIONS[current_brightness_index]

def turn_off_display():
    DISPLAY.brightness = 0

def turn_on_display():
    DISPLAY.brightness = BRIGHTNESS_OPTIONS[current_brightness_index]

# ---------- I2C SETUP -------------#
i2c = I2C()

# ---------- ACCELEROMETER / ORIENTATION SETUP -------------#
debug('Starting accelerometer')
accelerometer = Accelerometer(i2c)

orientation = Orientation(accelerometer)
def cb_to_face_down(orientation_name):
    turn_off_display()
    enqueue_action_payload(game_logic.get_action_payload_force_pause())
def cb_from_face_down(orientation_name):
    turn_on_display()
    enqueue_action_payload(game_logic.get_action_payload_force_unpause())
def cb_to_upside_down(orientation_name):
    Gui.set_rotation(180)
def cb_to_right(orientation_name):
    Gui.set_rotation(90)
def cb_to_left(orientation_name):
    Gui.set_rotation(270)
def cb_to_standing(orientation_name):
    Gui.set_rotation(0)

orientation.set_callback(ORIENTATION_RIGHT, cb_to_right, None)
orientation.set_callback(ORIENTATION_LEFT, cb_to_left, None)
orientation.set_callback(ORIENTATION_STANDING, cb_to_standing, None)
orientation.set_callback(ORIENTATION_UPSIDE_DOWN, cb_to_upside_down, None)
orientation.set_callback(ORIENTATION_FACE_DOWN, cb_to_face_down, cb_from_face_down)
orientation.loop()

# ---------- SPLASH SETUP -------------#
debug("Creating Splash")
Gui.create_root_splash()
Gui.show_splash()

# ---------- REMAINING IMPORTS -------------#
Gui.set_splash_text('Loading libraries')

from time import monotonic, sleep
from alarm import light_sleep_until_alarms, time
from gc import collect

from internet import MQTT, http_get_json, connect_to_wifi
from buttons import Buttons
from game_logic import GameLogic
from piezo import beep_error, beep_success, beep_shake

# ---------- GUI SETUP -------------#
orientation.loop()
Gui.set_splash_text('Loading fonts')
Gui.load_fonts()
orientation.loop()
Gui.set_splash_text('Creating graphics')
Gui.create_root_main()

# ---------- GAME LOGIC SETUP -------------#
game_logic = GameLogic()

# ---------- BUTTONS SETUP -------------#
debug('Creating buttons')
buttons = Buttons({
    BUTTON: False,
    D1: True,
    D2: True,
})

payload_to_send = None
def enqueue_action_payload(payload, success_sound=beep_success, failure_sound=beep_error):
    global payload_to_send
    if payload != None:
        success_sound()
        payload_to_send = payload
    else:
        failure_sound()

def send_action_payload_loop():
    global payload_to_send
    if payload_to_send != None:
        Gui.set_syncing(True)
        old_game_state_version = game_logic.game_state_version
        mqtt.publish(payload_to_send)
        payload_to_send = None
        poll_mqtt_until_game_state_changes(old_game_state_version)


def button_d0_callback():
    enqueue_action_payload(game_logic.get_action_payload_primary())

def button_d1_callback():
    enqueue_action_payload(game_logic.get_action_payload_secondary())

def button_d2_callback():
    enqueue_action_payload(game_logic.get_action_payload_admin())

buttons.set_callback(BUTTON, button_d0_callback)
buttons.set_callback(D1, button_d1_callback)
buttons.set_callback(D2, button_d2_callback)

# ---------- BATTERY SETUP -------------#
orientation.loop()
Gui.set_splash_text('Monitoring battery')
from adafruit_max1704x import MAX17048
battery_device = MAX17048(i2c)

# ---------- ACCELERATION CALLBACK SETUP SETUP -------------#
move_start_acceleration = None
def cb_movement(acceleration):
    global move_start_acceleration
    if move_start_acceleration == None:
        move_start_acceleration = acceleration
    orientation.loop()
    pass

def cb_inactivity(acceleration):
    orientation.loop(force=True)

def cb_shake():
    enqueue_action_payload(game_logic.get_action_payload_undo(), success_sound=beep_shake)

accelerometer.set_movement_callback(cb_movement)
accelerometer.set_inactivity_callback(cb_inactivity)
accelerometer.set_shake_callback(cb_shake)

# ---------- CURRENT TIME SETUP -------------#
connect_to_wifi()
Gui.set_splash_text('Getting current time')
time_json = http_get_json('http://worldtimeapi.org/api/timezone/Etc/UTC')
game_logic.set_current_unix_time(time_json['unixtime'])

# ---------- MQTT SETUP -------------#
def on_mqtt_message(msg):
    game_logic.handle_state_update(msg)
    game_logic.loop()

debug('Creating MQTT client')
mqtt = MQTT(on_mqtt_message)
def poll_mqtt(force=False, fallback_message=None):
    global last_poll_ts
    if force or monotonic() - last_poll_ts > (MQTT_POLL_FREQ-1):
        Gui.set_syncing(True)
        DISPLAY.refresh()
        mqtt.poll_for_new_messages(fallback_message)
        Gui.set_syncing(False)
        DISPLAY.refresh()
        last_poll_ts = monotonic()

def poll_mqtt_until_game_state_changes(old_game_state_version):
    global last_poll_ts
    Gui.set_syncing(True)
    DISPLAY.refresh()
    ts = monotonic()
    while old_game_state_version == game_logic.game_state_version and monotonic() - ts < 4:
        sleep(1)
        mqtt.poll_for_new_messages()
    Gui.set_syncing(False)
    DISPLAY.refresh()
    last_poll_ts = monotonic()

try:
    orientation.loop()
    poll_mqtt(force=True, fallback_message=None)

    # ---------- MAIN LOOP -------------#
    auto_press_count = 1
    loop_count = 0
    while True:
        loop_count += 1
        Gui.set_battery(battery_device.cell_percent)
        alarms = buttons.get_alarms()
        alarms.append(accelerometer.accelerometer_interrupt_alarm)
        time_alarm = time.TimeAlarm(monotonic_time=monotonic() + MQTT_POLL_FREQ)
        alarms.append(time_alarm)
        activated_alarm = light_sleep_until_alarms(*alarms)
        if activated_alarm == accelerometer.accelerometer_interrupt_alarm:
            accelerometer.loop()
        elif activated_alarm == time_alarm:
            poll_mqtt()
        buttons.loop()
        game_logic.loop()
        send_action_payload_loop()
        DISPLAY.refresh()
        collect()
except Exception as e:
    Gui.set_rotation(0)
    DISPLAY.brightness = 1
    print(dir(e))
    raise e