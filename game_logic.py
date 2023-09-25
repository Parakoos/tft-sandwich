from debug import debug
import json
from time import monotonic
from math import floor
from gui import Gui, SAND_COLOR_OUT_OF_TIME

# Constants
STATE_PLAYING = 'pl'
STATE_ADMIN = 'ad'
STATE_PAUSE = 'pa'
STATE_START = 'st'
STATE_FINISHED = 'en'
STATE_NOT_CONNECTED = 'nc'
STATE_RUNNING = 'ru'
STATE_NOT_RUNNING = 'nr'

TIMER_MODE_COUNT_UP = 'cu'
TIMER_MODE_COUNT_DOWN = 'cd'
TIMER_MODE_SAND_TIMER = 'st'
TIMER_MODE_NO_TIMER = 'nt'

DISPLAY_MODE_SPLASH = 'Splash'
DISPLAY_MODE_TITLES_ONLY = 'Titles Only'
DISPLAY_MODE_TITLES_AND_TIMES = 'Titles and Times'

def simplify_color(color):
    return (simplify_color_part(color[0]), simplify_color_part(color[1]), simplify_color_part(color[2]))

def simplify_color_part(color_part):
    return (color_part//86)*127

def sec_to_text(s):
    sec_abs = abs(s)
    t = 0
    if (sec_abs > 5460):
        t = '{} h, {} min'.format(floor(sec_abs / 3600), round((sec_abs % 3600) / 60))
    elif (sec_abs > 99):
        t = '{} min'.format(round(sec_abs / 60))
    else:
        t = '{} sec'.format(round(sec_abs))

    if (s < 0):
        return '({})'.format(t)
    else:
        return t

def get_state_int(state, key, default=0):
    return int(state[key]) if key in state and state[key] != None else default

def get_state_string(state, key, default=""):
    return state[key] if key in state and state[key] != None else default

def get_action_string(actions, key):
    return actions[key]['action'] if key in actions and actions[key] != None else None

class GameLogic():
    def __init__(self):
        self.display_mode = DISPLAY_MODE_SPLASH
        self.game_state_version = -1          # The last version of the state, used to prevent doing actions against old states. Must be sent with each command.
        self.timer_mode = None           # Current timer-mode (cd/cu/st/nt for Count-Down/Up, SandTimer, No Timer)
        self.state=''                       # The current state. SandTimer,
                                            # Sand, ru/nr/pa/en for running, not running, paused or end
                                            # Not Sand, st/en/pa/ad/pl for start, end, pause, admin or playing
        self.color = None                # (not sand) The current or next-up player color
        self.name=""                     # (not sand) The current or next-up player name

        self.turn_time_sec=0             # Count-Up, time taken this turn or pause time or admin time
                                         # Count-Down, same as above, but negative values during Delay Time
                                         # Sand, time taken out of the sand timer

        self.player_time_sec=0           # Count-Up, total time taken, or blank for admin/pause time
                                         # Count-Down, remaining time bank, or blank for admin/pause time
                                         # Sand, sand-timer reset size

        self.total_play_time_sec=0       # Count-Up/Down, total play time, not counting this turn and not admin/pause time

        self.action_primary = None       # Different actions. Either None or a string starting with 'game/{action}' that
        self.action_secondary = None     # can be sent to the MQTT commands queue to issue commands
        self.action_admin = None         # Also used to show the right icons.
        self.action_pause = None         #

        self.update_ts=monotonic()       # When did we last get an update from SGT?
        self.last_shake_ts=0             # When did we last shake the playground?
        self.incomplete_line_read=''     # If we've read data not ending in new line, store it here for now
        self.last_read_state='YO!'       # Last completed line read. Used to avoid duplicate lines.
        self.last_screen_update_ts = 0   # Used to slow down screen updates to once a second
        self.is_covered = False          # Keep track of if we are currently covering the proximity sensor
        self.covered_ts = None           # When was the sensor covered?
        self.orientation = None          # Up, Down, Front, Back, Left or Right (string)
        self.orientation_tmp = None      # What is the latest detected orientation
        self.orientation_tmp_ts = 0      # When did we set the self.orientation_tmp value.
        self.unix_time_offset = 0        # How much to add to monotonic() to get current unix time

    def set_current_unix_time(self, time_unix_sec):
        now = round(monotonic())
        debug(f"Current Unix Time: {time_unix_sec} at mono {now}")
        self.unix_time_offset = time_unix_sec - now

    def get_current_unix_time(self):
        now = round(monotonic())
        ts = self.unix_time_offset + now
        return ts

    def handle_state_update(self, state_json):
        if (self.last_read_state == state_json):
            return

        self.last_read_state = state_json
        debug(f"New State: {state_json}")
        state = json.loads(state_json) if state_json != None and state_json != "" else {}
        state_ts_unix = get_state_int(state, 'ts', 0)
        local_ts_unix = self.get_current_unix_time()
        age_of_state = local_ts_unix - state_ts_unix
        self.update_ts=round(monotonic())-age_of_state
        self.last_screen_update_ts = 0
        self.game_state_version = get_state_int(state, 'gameStateVersion', -1)
        self.turn_time_sec = get_state_int(state, 'turnTime')
        self.player_time_sec = get_state_int(state, 'playerTime')
        self.total_play_time_sec = get_state_int(state, 'totalPlayTime')
        self.name = get_state_string(state, 'name', "(no name)")
        color_hex = get_state_string(state, 'color')
        self.color = simplify_color((int(color_hex[0:2],16),int(color_hex[2:4],16),int(color_hex[4:6],16))) if len(color_hex) == 6 else (255,255,255)

        actions = state['actions'] if 'actions' in state and state['actions'] != None else {}
        self.action_primary = get_action_string(actions, 'primary')
        self.action_secondary = get_action_string(actions, 'secondary')
        self.action_admin = get_action_string(actions, 'admin')
        self.action_pause = get_action_string(actions, 'pause')

        new_timer_mode = get_state_string(state, 'timerMode', TIMER_MODE_COUNT_UP)
        new_state = get_state_string(state, 'state', STATE_NOT_CONNECTED)

        if (new_timer_mode != self.timer_mode or self.state != new_state):
            if (new_state != DISPLAY_MODE_TITLES_ONLY and (
                new_state == STATE_FINISHED
                    or new_state == STATE_NOT_CONNECTED
                    or new_state == TIMER_MODE_NO_TIMER)):
                self.switch_to_titles_only_gui()
            elif new_state != DISPLAY_MODE_TITLES_AND_TIMES:
                self.switch_to_titles_and_times_gui()

        if new_timer_mode != self.timer_mode:
            self.timer_mode = new_timer_mode

        self.state = new_state
        if self.state == STATE_PLAYING:
            self.switch_to_playing()
        elif self.state == STATE_NOT_CONNECTED:
            self.switch_to_not_connected()
        elif self.state == STATE_ADMIN:
            self.switch_to_admin_time()
        elif self.state == STATE_PAUSE:
            self.switch_to_paused()
        elif self.state == STATE_FINISHED:
            self.switch_to_end()
        elif self.state == STATE_START:
            self.switch_to_start()
        elif self.state == STATE_RUNNING:
            self.switch_to_sandtimer_running()
        elif self.state == STATE_NOT_RUNNING:
            self.switch_to_sandtimer_not_running()
        else:
            raise Exception(f"Unknown state: {self.state}")

        Gui.set_primary_action_icon(self.action_primary[5:] if self.action_primary != None else None)
        Gui.set_secondary_action_icon(self.action_secondary[5:] if self.action_secondary != None else None)
        Gui.set_admin_action_icon(self.action_admin[5:] if self.action_admin != None else None)

    def switch_to_titles_only_gui(self):
        # debug("Switch to TITLES ONLY")
        Gui.show_titles_only()

    def switch_to_titles_and_times_gui(self):
        # debug("Switch to TITLES AND TIMES")
        Gui.show_titles_and_times()

    def switch_to_playing(self):
        # debug(f"Switch to PLAYING! Name: {self.name} - Color: {self.color}")
        Gui.set_title(self.name)
        Gui.set_background(self.color)

    def switch_to_admin_time(self):
        # debug("Switch to Admin Time")
        Gui.set_title("Admin Time", self.name)
        Gui.set_total_time("")
        Gui.set_background(self.color)

    def switch_to_paused(self):
        # debug("Switch to Paused")
        Gui.set_title("Paused", self.name)
        Gui.set_total_time("")
        Gui.set_background(self.color)

    def switch_to_start(self):
        # debug("Switch to Start")
        Gui.set_turn_time("")
        Gui.set_total_time("")
        Gui.set_title('Starting', self.name)
        Gui.set_background(self.color)

    def switch_to_not_connected(self):
        # debug("Switch to Not Connected")
        Gui.show_titles_only()
        self.color = (0,0,0)
        Gui.set_turn_time("")
        Gui.set_total_time("")
        Gui.set_title('No game in view', "Open game with mqtt on")
        Gui.set_background(self.color)

    def switch_to_end(self):
        # debug("Switch to End")
        self.color = (0,0,0)
        Gui.set_title("Game Over")
        Gui.set_background(self.color)

    def switch_to_sandtimer_running(self):
        # debug("Switch to Sand Timer Running")
        Gui.set_title('', sec_to_text(self.player_time_sec))

    def switch_to_sandtimer_not_running(self):
        # debug("Switch to Sand Timer Not Running")
        Gui.set_title('', sec_to_text(self.player_time_sec))

    def get_action_payload(self, action):
        return json.dumps({"gameStateVersion": self.game_state_version, "action": action}) if action != None else None

    def get_action_payload_primary(self):
        return self.get_action_payload(self.action_primary)

    def get_action_payload_secondary(self):
        return self.get_action_payload(self.action_secondary)

    def get_action_payload_admin(self):
        return self.get_action_payload(self.action_admin)

    def get_action_payload_pause(self):
        return self.get_action_payload(self.action_pause)

    def get_action_payload_undo(self):
        return self.get_action_payload('game/undo' if self.state in [STATE_PLAYING, STATE_ADMIN, STATE_PAUSE] else None)

    def get_action_payload_force_pause(self):
        return self.get_action_payload(self.action_pause if self.action_pause == 'game/pause' else None)

    def get_action_payload_force_unpause(self):
        possible_actions = [self.action_pause, self.action_primary, self.action_admin]
        return self.get_action_payload('game/unpause' if 'game/unpause' in possible_actions else None)

    def loop(self):
        now = round(monotonic())
        if ((now - self.last_screen_update_ts) < 1) :
            return
        self.last_screen_update_ts = now

        if self.timer_mode == None:
            return

        if self.timer_mode == TIMER_MODE_COUNT_UP:
            if self.state in [STATE_PLAYING, STATE_ADMIN, STATE_PAUSE]:
                time_added_by_monotonic = now - self.update_ts
                turn_time = self.turn_time_sec + time_added_by_monotonic
                Gui.set_turn_time(sec_to_text(turn_time))
                if self.state == STATE_PLAYING:
                    player_time = time_added_by_monotonic + self.player_time_sec
                    total_play_time = (time_added_by_monotonic + self.total_play_time_sec)
                    percent = round(100 * player_time / total_play_time) if total_play_time != 0 else 0
                    Gui.set_total_time('{}%'.format(percent))
            elif self.state in [STATE_START, STATE_FINISHED, STATE_NOT_CONNECTED]:
                pass
            else:
                raise Exception(f'Unknown state: {self.state}')

        elif self.timer_mode == TIMER_MODE_COUNT_DOWN:
            if self.state in [STATE_PLAYING, STATE_ADMIN, STATE_PAUSE]:
                time_added_by_monotonic = now - self.update_ts
                turn_time = self.turn_time_sec + time_added_by_monotonic
                Gui.set_turn_time(sec_to_text(turn_time))
                if self.state == STATE_PLAYING:
                    remaining_time_bank = self.player_time_sec
                    if (self.turn_time_sec < 0):
                        remaining_time_bank -= max(0, time_added_by_monotonic + self.turn_time_sec)
                    else:
                        remaining_time_bank -= time_added_by_monotonic
                    Gui.set_total_time(sec_to_text(remaining_time_bank))
            elif self.state in [STATE_START, STATE_FINISHED, STATE_NOT_CONNECTED]:
                pass
            else:
                raise Exception(f"Unknown state: {self.state}")

        elif self.timer_mode == TIMER_MODE_NO_TIMER:
            if self.state in [STATE_PLAYING, STATE_ADMIN, STATE_PAUSE, STATE_START, STATE_FINISHED, STATE_NOT_CONNECTED]:
                pass
            else:
                raise Exception(f'Unkown state: {self.state}')

        elif self.timer_mode == TIMER_MODE_SAND_TIMER:
            if self.state == STATE_RUNNING:
                time_added_by_monotonic = now - self.update_ts
                turn_time = self.turn_time_sec + time_added_by_monotonic
                remaining_time = max(self.player_time_sec - turn_time, 0)
                if (remaining_time == 0):
                    Gui.set_background(SAND_COLOR_OUT_OF_TIME)
                    Gui.set_title('(still running)', sec_to_text(self.player_time_sec))
                    Gui.set_turn_time("Out of Time!")
                else:
                    Gui.update_sandtimer_position(remaining_time/ self.player_time_sec)
                    Gui.set_turn_time(sec_to_text(remaining_time))
            elif self.state == STATE_NOT_RUNNING:
                remaining_time = max(self.player_time_sec - self.turn_time_sec, 0)
                if (remaining_time == 0):
                    Gui.set_background(SAND_COLOR_OUT_OF_TIME)
                    Gui.set_title('(stopped)', sec_to_text(self.player_time_sec))
                    Gui.set_turn_time("Out of Time!")
                else:
                    Gui.update_sandtimer_position(remaining_time/ self.player_time_sec)
                    Gui.set_turn_time(sec_to_text(remaining_time))
            elif self.state == STATE_PAUSE:
                time_added_by_monotonic = now - self.update_ts
                turn_time = self.turn_time_sec + time_added_by_monotonic
                Gui.set_background((0, 0, 0))
                Gui.set_turn_time(sec_to_text(turn_time))
            elif self.state in [STATE_FINISHED, STATE_NOT_CONNECTED]:
                pass
            else:
                raise Exception(f'Unkown state: {self.state}')
        else:
            raise Exception(f'Unkown timer mode: {self.timer_mode}')