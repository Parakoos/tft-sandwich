from debug import debug
from ssl import create_default_context
from socketpool import SocketPool
from wifi import radio
from adafruit_minimqtt.adafruit_minimqtt import MQTT as ADA_MQTT
from settings import WIFI_SSID, WIFI_PASSWORD, MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_SUBSCRIBE_TOPIC, MQTT_PUBLISH_TOPIC
from gui import Gui
from adafruit_requests import Session

DISABLED = False

pool = SocketPool(radio)
ssl_context = create_default_context()
is_connected = False

def connect_to_wifi():
        while True:
            try:
                Gui.show_splash()
                Gui.set_splash_text(f"Connecting to WIFI ({WIFI_SSID})")
                radio.connect(WIFI_SSID, WIFI_PASSWORD)
                break
            except Exception as e:
                Gui.show_error(e)


def http_get_json(url):
    requests = Session(pool, ssl_context)
    response = requests.get(url)
    return response.json()

class MQTT:
    def __init__(self, on_message_callback):
        # If you need to use certificate/key pair authentication (e.g. X.509), you can load them in the
        # ssl context by uncommenting the lines below and adding the following keys to the "secrets"
        # dictionary in your secrets.py file:
        # "device_cert_path" - Path to the Device Certificate
        # "device_key_path" - Path to the RSA Private Key
        # ssl_context.load_cert_chain(
        #     certfile=secrets["device_cert_path"], keyfile=secrets["device_key_path"]
        # )

        self.mqtt_client = ADA_MQTT(
            broker=MQTT_HOST,
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            socket_pool=pool,
            ssl_context=ssl_context,
            is_ssl=True,
        )

        self.on_message_callback = on_message_callback
        self.mqtt_client.on_connect = self.connected
        self.mqtt_client.on_disconnect = self.disconnected
        self.mqtt_client.on_message = self.message

    def connect(self):
        if DISABLED:
            return
        while True:
            try:
                Gui.set_splash_text(f"Connecting to MQTT")
                self.mqtt_client.connect()
                debug("Connected to MQTT!")
                break
            except Exception as e:
                Gui.show_error(e)


    def connected(self, client, userdata, flags, rc):
        debug(f"Connected to MQTT! Listening for topic changes on {MQTT_SUBSCRIBE_TOPIC}")
        client.subscribe(MQTT_SUBSCRIBE_TOPIC)

    def disconnected(self, client, userdata, rc):
        debug("Disconnected from MQTT!")

    def message(self, client, topic, message):
        self.on_message_callback(message)

    def publish(self, value):
        if DISABLED:
            return

        if not self.mqtt_client.is_connected():
            self.connect()

        while True:
            try:
                self.mqtt_client.publish(MQTT_PUBLISH_TOPIC, value)
                break
            except Exception as e:
                Gui.show_error(e)



    def poll_for_new_messages(self, fallback_message=None):
        if DISABLED:
            return
        if not self.mqtt_client.is_connected():
            self.connect()
        while True:
            try:
                response_codes = self.mqtt_client.loop()
                if fallback_message != None and (response_codes == None or len(response_codes) == 0):
                    self.on_message_callback(fallback_message)
                break
            except ConnectionError as e:
                print(f"ConnectionError: {e.errno}, {e.strerror}")
                Gui.show_error(e)
            except Exception as e:
                Gui.show_error(e)
