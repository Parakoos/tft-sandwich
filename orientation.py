from debug import debug
from time import monotonic
from settings import ORIENTATION_RIGHT, ORIENTATION_LEFT, ORIENTATION_UPSIDE_DOWN, ORIENTATION_STANDING, ORIENTATION_FACE_DOWN, ORIENTATION_FACE_UP, ORIENTATION_ON_THRESHOLD, ORIENTATION_OFF_THRESHOLD

class Orientation:
    def __init__(self, accelerometer):
        self.accelerometer = accelerometer
        self.orientation = None          # Up, Down, Front, Back, Left or Right (string)
        self.last_loop_ts = -1000
        self.rotation_start_vals = None
        # self.orientation_tmp = None      # What is the latest detected orientation
        # self.orientation_tmp_ts = 0      # When did we set the self.orientation_tmp value.
        self.callbacks = {}

    def set_callback(self, orientation, to_callback, from_callback):
        self.callbacks[orientation] = (to_callback, from_callback)

    def loop(self, force=False):
        if not force and (monotonic() - self.last_loop_ts) < 2:
            # debug("skip orient loop")
            return

        acceleration = self.accelerometer.get_acceleration()
        x_orient = self.check_orientation_axis(acceleration[0], ORIENTATION_RIGHT, ORIENTATION_LEFT)
        y_orient = self.check_orientation_axis(acceleration[1], ORIENTATION_UPSIDE_DOWN, ORIENTATION_STANDING)
        z_orient = self.check_orientation_axis(acceleration[2], ORIENTATION_FACE_DOWN, ORIENTATION_FACE_UP)
        new_orient = x_orient or y_orient or z_orient

        if self.orientation != None and self.orientation != new_orient and self.orientation in self.callbacks and self.callbacks[self.orientation][1]:
            # Leave current orientation
            self.callbacks[self.orientation][1](self.orientation)

        if new_orient != None and self.orientation != new_orient and new_orient in self.callbacks and self.callbacks[new_orient][0]:
            # Enter new orientation
            self.callbacks[new_orient][0](new_orient)
            self.orientation = new_orient

        self.last_loop_ts = monotonic()

    def check_orientation_axis(self, value, pos_orientation, neg_orientation):
        if value > ORIENTATION_ON_THRESHOLD:
            return pos_orientation
        elif -value > ORIENTATION_ON_THRESHOLD:
            return neg_orientation
        else:
            return None