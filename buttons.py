from alarm import pin
from digitalio import DigitalInOut, Pull

class Buttons():
    def __init__(self, pins_to_pressed_bool_map):
        self.pins_to_pressed_bool_map = pins_to_pressed_bool_map
        self.callbacks = {}

    def get_alarms(self):
        alarms = []
        for _pin, pressed_val in self.pins_to_pressed_bool_map.items():
            alarms.append(pin.PinAlarm(pin=_pin, value=pressed_val, pull=True))
        return alarms

    def set_callback(self, pin, callback):
        self.callbacks[pin] = callback

    def loop(self):
        for pin, callback in self.callbacks.items():
            button = DigitalInOut(pin)
            pull = Pull.DOWN if self.pins_to_pressed_bool_map[pin] else Pull.UP
            button.switch_to_input(pull=pull)
            if button.value == self.pins_to_pressed_bool_map[pin]:
                callback()
                while button.value == self.pins_to_pressed_bool_map[pin]:
                    pass
                button.deinit()
                return
            else:
                button.deinit()