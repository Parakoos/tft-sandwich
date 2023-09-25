
from board import A1

# Set your wifi credentials here
WIFI_SSID = "ENTER YOUR WIFI ACCESS POINT NAME HERE"
WIFI_PASSWORD = "ENTER YOUR WIFI ACCESS POINT PASSWORD HERE"

# Setup your MQTT credentials here. Get them from https://sharedgametimer.com/mqtt
SGT_USER_ID = ""
MQTT_HOST = ""
MQTT_PORT = 8883
# MQTT_PATH = "/mqtt"
MQTT_SUBSCRIBE_TOPIC = SGT_USER_ID + "/game"
MQTT_PUBLISH_TOPIC = SGT_USER_ID + "/commands"
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
MQTT_POLL_FREQ = 5

BRIGHTNESS_OPTIONS = [0.06, 0.2, 0.4, 0.7, 1.0]    # The different brightnesses to cycle through
BRIGHTNESS_INITIAL_INDEX = 4       # 0-indexed. Which brightness to start with.

PIEZO_PIN = A1

MOVEMENT_THRESHOLD = 18
INACTIVITY_THRESHOLD = 18
INACTIVITY_TIME = 4

ORIENTATION_ON_THRESHOLD = 8.0      # 0-10. Higher number, less sensitive.
ORIENTATION_OFF_THRESHOLD = 4.0     # 0-10. Higher number, more sensitive.
ORIENTATION_RIGHT = 'Right'         # The names of the various directions.
ORIENTATION_LEFT = 'Left'
ORIENTATION_STANDING = 'Standing'
ORIENTATION_UPSIDE_DOWN = 'Upside Down'
ORIENTATION_FACE_DOWN = 'Face Down'
ORIENTATION_FACE_UP = 'Face Up'