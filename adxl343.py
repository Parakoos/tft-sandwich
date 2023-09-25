from board import A4
from alarm import pin
from time import monotonic
from adafruit_adxl34x import ADXL343, _REG_INT_ENABLE, _REG_ACT_INACT_CTL, _REG_THRESH_INACT, _REG_TIME_INACT, _INT_INACT
from settings import MOVEMENT_THRESHOLD, INACTIVITY_THRESHOLD, INACTIVITY_TIME

class Accelerometer:
    def __init__(self, i2c):
        while True:
            try:
                self.accelerometer = ADXL343(i2c)
                self.accelerometer.enable_motion_detection(threshold=MOVEMENT_THRESHOLD)
                self.accelerometer_interrupt_alarm = pin.PinAlarm(pin=A4, value=True)
                self.movement_callback = None
                self.inactivity_callback = None
                self.shake_callback = None
                self.inactivity_interrupt_active = False
                self.shake_progression = [0,0,0]
                self.shake_direction_changes = []
                break
            except Exception as e:
                print(e)
                print('Error caught when starting accelerometer. Retrying...')

    def set_movement_callback(self, callback):
        self.movement_callback = callback

    def set_inactivity_callback(self, callback):
        self.inactivity_callback = callback

    def set_shake_callback(self, callback):
        self.shake_callback = callback

    def loop(self):
        events = self.accelerometer.events
        if events["motion"]:
            if self.inactivity_interrupt_active == False:
              self.enable_inaction_detection(threshold=INACTIVITY_THRESHOLD, time=INACTIVITY_TIME)
              self.inactivity_interrupt_active = True

            if self.movement_callback != None:
                self.movement_callback(self.accelerometer.acceleration)

            now = monotonic()
            two_sec_ago = now - 2

            for i, ts in enumerate(self.shake_direction_changes):
                if ts >= two_sec_ago:
                    if i > 0:
                        self.shake_direction_changes = self.shake_direction_changes[i:]
                    break

            for i, acc in enumerate(self.accelerometer.acceleration):
                if acc > 8:
                    if self.shake_progression[i] < 0:
                        self.shake_direction_changes.append(now)
                    self.shake_progression[i] = 1
                elif acc < -8:
                    if self.shake_progression[i] > 0:
                        self.shake_direction_changes.append(now)
                    self.shake_progression[i] = -1

            if len(self.shake_direction_changes) > 4:
                self.shake_direction_changes = []
                if self.shake_callback != None:
                    self.shake_callback()
        else:
            self.disable_inaction_detection()
            self.inactivity_interrupt_active = False
            self.shake_progression = [0,0,0]
            self.shake_direction_changes = []

            if self.inactivity_callback != None:
                self.inactivity_callback(self.accelerometer.acceleration)

    def get_acceleration(self):
        return self.accelerometer.acceleration

    def enable_inaction_detection(self, *, threshold: int = 18, time: int = 25):
        """
        The normal adxl343 library does not expose the ability to detect inactivity.
        This code follows the format of enable_motion_detection.
        """
        active_interrupts = self.accelerometer._read_register_unpacked(_REG_INT_ENABLE)

        self.accelerometer._write_register_byte(_REG_INT_ENABLE, 0x0)  # disable interrupts for setup
        self.accelerometer._write_register_byte(_REG_ACT_INACT_CTL, 0b01111111)  # enable activity on X,Y,Z
        self.accelerometer._write_register_byte(_REG_THRESH_INACT, threshold)
        self.accelerometer._write_register_byte(_REG_TIME_INACT, time)
        self.accelerometer._write_register_byte(_REG_INT_ENABLE, _INT_INACT)  # Inactive interrupt only

        active_interrupts |= _INT_INACT
        self.accelerometer._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self.accelerometer._enabled_interrupts["inactivity"] = True

    def disable_inaction_detection(self) -> None:
        """
        Disable motion detection
        """
        active_interrupts = self.accelerometer._read_register_unpacked(_REG_INT_ENABLE)
        active_interrupts &= ~_INT_INACT
        self.accelerometer._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self.accelerometer._enabled_interrupts.pop("inactivity")