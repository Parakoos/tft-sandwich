from debug import debug
from displayio import Group, OnDiskBitmap, TileGrid, CIRCUITPYTHON_TERMINAL
from math import sqrt
from board import DISPLAY, D1, D2
from digitalio import DigitalInOut, Pull
from text import Text
from terminalio import FONT as terminal_font

SCREEN_LONG_EDGE = 240
SCREEN_SHORT_EDGE = 135

SAND_COLOR_OUT_OF_TIME = (255, 0, 0)
SAND_COLOR_TIME_LEFT = (0, 255, 0)
SAND_COLOR_TIME_USED = (120, 120, 255)

class Gui:
    __root_splash = None
    __splash_text = None
    __splash_image_big = None
    __splash_image_small = None
    __root_main = None
    __font_time = None
    __font_time_glyphs = None
    __font_large = None
    __font_small = None
    __font_large_small_glyphs = None
    __curr_bg_color = None
    __curr_fg_color = (0, 255, 0)
    __bg_rect = None
    __bg_rect_sandtimer = None
    __bg_rect_group = None
    __bg_rect_sandtimer_group = None

    __all_texts = []
    __text_title = None
    __text_sub_title = None
    __text_turn_time = None
    __text_total_time = None

    __all_icons = []
    __icon_set_battery = None
    __icon_set_primary = None
    __icon_set_secondary = None
    __icon_set_admin = None
    __icon_set_state = None

    __title_only_positions = None
    __title_only_max_lines = None
    __sub_title_only_positions = None
    __sub_title_only_max_lines = None
    __title_and_times_positions = None
    __title_and_times_max_lines = None
    __sub_title_and_times_positions = None
    __sub_title_and_times_max_lines = None

    def __init__(self) -> None:
        raise Exception('Do not initialize this class')

    # ============== INIT ===================
    def load_fonts():
        from adafruit_bitmap_font import bitmap_font

        Gui.__font_time_glyphs = b'0123456789hminsec ,-'
        Gui.__font_time = bitmap_font.load_font("/fonts/Arial-Bold-24-reduced.bdf")
        Gui.__font_time.load_glyphs(Gui.__font_time_glyphs)

        Gui.__font_large_small_glyphs = '0123456789abcdefghijklmnopqrstuvwxyzåäöABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ !"#%\'()-,./:?'
        Gui.__font_small = bitmap_font.load_font("/fonts/helvR14-reduced.bdf")
        Gui.__font_small.load_glyphs(Gui.__font_large_small_glyphs)

        Gui.__font_large = bitmap_font.load_font("/fonts/helvR18-reduced.bdf")
        Gui.__font_large.load_glyphs(Gui.__font_large_small_glyphs)

    def __get_sgt_icon_placement_info(icon_bitmap):
        result = {"horizontal": {"icon": {}, "pre": {}, "post": {}}, "vertical": {"icon": {}, "pre": {}, "post": {}}}

        # horizontal
        icon_padding = round((SCREEN_SHORT_EDGE - icon_bitmap.height)/2)
        half_empty_space = round((SCREEN_LONG_EDGE - icon_bitmap.width)/2)
        result["horizontal"]["pre"] = (0, 0, half_empty_space, SCREEN_SHORT_EDGE)
        result["horizontal"]["icon"] = (half_empty_space, icon_padding, icon_bitmap.width, icon_bitmap.height)
        x, y, width, height = result["horizontal"]["icon"]
        result["horizontal"]["post"] = (x+width, 0, half_empty_space, SCREEN_SHORT_EDGE)

        # vertical
        icon_padding = round((SCREEN_SHORT_EDGE - icon_bitmap.width)/2)
        half_empty_space = round((SCREEN_LONG_EDGE - icon_bitmap.height)/2)
        result["vertical"]["pre"] = (0, 0, SCREEN_SHORT_EDGE, half_empty_space)
        result["vertical"]["icon"] = (icon_padding, half_empty_space, icon_bitmap.width, icon_bitmap.height)
        x, y, width, height = result["vertical"]["icon"]
        result["vertical"]["post"] = (0, y+height, SCREEN_SHORT_EDGE, half_empty_space)
        return result

    def create_root_splash():
        Gui.__root_splash = Group()

        odb_small = OnDiskBitmap('sgt-icon-small.bmp')
        spacing = Gui.__get_sgt_icon_placement_info(odb_small)
        x, y, width, height = spacing["horizontal"]["icon"]
        Gui.__splash_image_small = TileGrid(odb_small, pixel_shader=odb_small.pixel_shader, x=x, y=y)
        Gui.__root_splash.append(Gui.__splash_image_small)
        x, y, width, height = spacing["horizontal"]["pre"]
        text_positions_h = (x+round(width/2)+10, y+round(height/2)-15)
        text_width_h = width

        odb_big = OnDiskBitmap('sgt-icon-big.bmp')
        spacing = Gui.__get_sgt_icon_placement_info(odb_big)
        x, y, width, height = spacing["vertical"]["icon"]
        Gui.__splash_image_big = TileGrid(odb_big, pixel_shader=odb_big.pixel_shader, x=x, y=y)
        Gui.__root_splash.append(Gui.__splash_image_big)
        x, y, width, height = spacing["vertical"]["pre"]
        text_positions_v = (x+round(width/2), y+round(height/2)-7)
        text_width_v = width

        Gui.__splash_text = Text(positions=(text_positions_h, text_positions_v), max_text_widths=(text_width_h, text_width_v), fonts=(terminal_font,), max_lines=(2,1), line_spacing=1)
        Gui.__splash_text.set_color(0xffffff)
        Gui.__root_splash.append(Gui.__splash_text.label)
        DISPLAY.root_group = Gui.__root_splash

    def create_root_main():
        if Gui.__root_main == None:
            from adafruit_display_shapes.rect import Rect
            Gui.__root_main = Group()
            Gui.__bg_rect = Rect(0, 0, 2, 2, fill=Gui.__curr_bg_color)
            Gui.__bg_rect_sandtimer = Rect(0, 0, 2, 2, fill=SAND_COLOR_TIME_USED)
            Gui.__bg_rect_group = Group(scale=120)
            Gui.__bg_rect_sandtimer_group = Group(scale=120)
            Gui.__bg_rect_group.append(Gui.__bg_rect)
            Gui.__bg_rect_sandtimer_group.append(Gui.__bg_rect_sandtimer)
            Gui.__root_main.append(Gui.__bg_rect_group)
            Gui.__root_main.append(Gui.__bg_rect_sandtimer_group)
            Gui.__bg_rect_sandtimer_group.y = -240

            HALF_LONG = round(SCREEN_LONG_EDGE / 2)
            HALF_SHORT = round(SCREEN_SHORT_EDGE / 2)
            ICON_LEN = 24
            ICON_MARGIN = 26

            Gui.__title_and_times_positions = ((HALF_LONG, 10), (HALF_SHORT, 30), )
            Gui.__title_and_times_max_lines = (1,2,)
            Gui.__sub_title_and_times_positions = ((HALF_LONG, SCREEN_SHORT_EDGE-24), (HALF_SHORT, SCREEN_LONG_EDGE-ICON_LEN-24), )
            Gui.__sub_title_and_times_max_lines = (1,2,)

            Gui.__title_only_positions = Gui.__title_and_times_positions
            Gui.__title_only_max_lines = (2,)
            Gui.__sub_title_only_positions = ((Gui.__sub_title_and_times_positions[0][0], Gui.__sub_title_and_times_positions[0][1]-15), (Gui.__sub_title_and_times_positions[1][0], Gui.__sub_title_and_times_positions[1][1]-15), )
            Gui.__sub_title_only_max_lines = (2,)

            max_text_widths = (SCREEN_LONG_EDGE-ICON_MARGIN*2, SCREEN_SHORT_EDGE)

            Gui.__text_title = Gui.__append_label(positions=Gui.__title_only_positions,
                                    max_lines=Gui.__title_only_max_lines,
                                    max_text_widths=max_text_widths,
                                    fonts=((Gui.__font_large, Gui.__font_large)),
                                    allowed_glyphs=Gui.__font_large_small_glyphs)

            Gui.__text_sub_title = Gui.__append_label(positions=Gui.__sub_title_only_positions,
                                    max_lines=Gui.__sub_title_only_max_lines,
                                    max_text_widths=max_text_widths,
                                    fonts=(Gui.__font_small, ),
                                    allowed_glyphs=Gui.__font_large_small_glyphs)

            Gui.__text_turn_time = Gui.__append_label(positions=((HALF_LONG, 53), (HALF_SHORT, HALF_LONG-24)),
                        max_text_widths=max_text_widths,
                        fonts=((Gui.__font_time, )),
                        allowed_glyphs=Gui.__font_time_glyphs)

            Gui.__text_total_time = Gui.__append_label(positions=((HALF_LONG, 100), (HALF_SHORT, HALF_LONG+35)),
                        max_text_widths=max_text_widths,
                        fonts=((Gui.__font_large,)),
                        allowed_glyphs=Gui.__font_large_small_glyphs)

            battery_positions = ((SCREEN_LONG_EDGE-22, SCREEN_SHORT_EDGE-26), (SCREEN_SHORT_EDGE-22, 2), (-2, SCREEN_SHORT_EDGE-26), (SCREEN_SHORT_EDGE-22, SCREEN_LONG_EDGE-26))
            battery_paths = {"0": 'icons/battery-outline.bmp',
                             "20": 'icons/battery-20.bmp',
                             "40": 'icons/battery-40.bmp',
                             "60": 'icons/battery-60.bmp',
                             "80": 'icons/battery-80.bmp',
                             "100": 'icons/battery.bmp',
                             }
            Gui.__icon_set_battery = Gui.__append_icon_set(battery_paths, battery_positions)

            state_positions = ((SCREEN_LONG_EDGE-24, 0), (0, 0), (0, 0), (0, SCREEN_LONG_EDGE-24))
            state_paths = {"sync": 'icons/sync.bmp'}
            Gui.__icon_set_state = Gui.__append_icon_set(state_paths, state_positions)

            primary_positions = ((0,                    0),
                                 (0,                    SCREEN_LONG_EDGE-24),
                                 (SCREEN_LONG_EDGE-24,  SCREEN_SHORT_EDGE-24),
                                 (SCREEN_SHORT_EDGE-24, 0))
            primary_paths = {
                "startTurn": "icons/play.bmp",
                "endTurn": "icons/arrow-right.bmp",
                "endRound": "icons/stop.bmp",
                "resumeTurn": "icons/play.bmp",
                "unpause": "icons/play.bmp",
                "startSandTimer": "icons/play.bmp",
                "stopSandTimer": "icons/stop.bmp",
                }
            Gui.__icon_set_primary =Gui.__append_icon_set(primary_paths, primary_positions)

            secondary_positions = ((0,                             round(SCREEN_SHORT_EDGE/2)-12),
                                   (round(SCREEN_SHORT_EDGE/2)-12, SCREEN_LONG_EDGE-24),
                                   (SCREEN_LONG_EDGE-24,           round(SCREEN_SHORT_EDGE/2)-12),
                                   (round(SCREEN_SHORT_EDGE/2)-12, 0))
            secondary_paths = {
                "pass": "icons/debug-step-over.bmp",
                "endRound": "icons/stop.bmp",
                "resumeTurn": "icons/play.bmp",
                "resetSandTimer": "icons/rotate-left.bmp",
                }
            Gui.__icon_set_secondary =Gui.__append_icon_set(secondary_paths, secondary_positions)

            admin_positions = ((0,                    SCREEN_SHORT_EDGE-24),
                               (SCREEN_SHORT_EDGE-24, SCREEN_LONG_EDGE-24),
                               (SCREEN_LONG_EDGE-24,  0),
                               (0,                    0))
            admin_paths = {
                "startMidTurnAdmin": "icons/pause.bmp",
                "endRound": "icons/stop.bmp",
                "unpause": "icons/play.bmp",
                "startSetupAdmin": "icons/clipboard-play-outline.bmp",
                }
            Gui.__icon_set_admin =Gui.__append_icon_set(admin_paths, admin_positions)

    # ============== MODE SWITCHERS ===================

    def show_splash():
        DISPLAY.root_group = Gui.__root_splash
        Gui.set_rotation(DISPLAY.rotation, force=True)

    def show_error(exception):
        current_group = DISPLAY.root_group
        error_group = Group()
        print(exception)
        print(dir(exception))
        if hasattr(exception, "errno"):
            print(f"Error Number: {exception.errno}")

        if hasattr(exception, "strerror"):
            print(f"Error String: {exception.strerror}")

        rotation_index = (int(DISPLAY.rotation / 90) % 2)

        image = None
        orientation = None
        x_shift_h = None # We want to nudge the text slightly in under the icon
        y_shift_pre = None # Need to move the text up a bit to make it look good
        y_shift_post = None

        if rotation_index == 0:
            orientation = "horizontal"
            image = OnDiskBitmap('sgt-icon-warning-small.bmp')
            x_shift_h = 7
            y_shift_pre = 20
            y_shift_post = 20
        else:
            orientation = "vertical"
            image = OnDiskBitmap('sgt-icon-warning-big.bmp')
            x_shift_h = 0
            y_shift_pre = 15
            y_shift_post = 10

        spacing = Gui.__get_sgt_icon_placement_info(image)
        x, y, width, height = spacing[orientation]["icon"]
        error_group.append(TileGrid(image, pixel_shader=image.pixel_shader, x=x, y=y))
        x, y, width, height = spacing[orientation]["pre"]
        text_pre_positions = (x+x_shift_h+round(width/2), y+round(height/2)-y_shift_pre)
        x, y, width, height = spacing[orientation]["post"]
        text_post_positions = (x-x_shift_h+round(width/2), y+round(height/2)-y_shift_post)

        text_pre = Text(positions=(text_pre_positions, text_pre_positions), max_text_widths=(13, 20), fonts=(terminal_font,), max_lines=(3,2), line_spacing=1)
        text_pre.set_color(0xffffff)
        text_pre.set_rotation_index(rotation_index)
        text_pre.set_text(f"{exception}")
        error_group.append(text_pre.label)

        text_post = Text(positions=(text_post_positions, text_post_positions), max_text_widths=(13, 20), fonts=(terminal_font,), max_lines=(3,2), line_spacing=1)
        text_post.set_color(0xffffff)
        text_post.set_rotation_index(rotation_index)
        text_post.set_text(f"Press D1 to retry or Reset to reboot")
        error_group.append(text_post.label)

        DISPLAY.root_group = error_group
        DISPLAY.refresh()

        button_d1 = DigitalInOut(D1)
        button_d1.switch_to_input(pull=Pull.DOWN)
        button_d2 = DigitalInOut(D2)
        button_d2.switch_to_input(pull=Pull.DOWN)
        while True:
            if button_d1.value:
                button_d1.deinit()
                button_d2.deinit()
                DISPLAY.root_group = current_group
                break
            elif button_d2.value:
                DISPLAY.root_group = CIRCUITPYTHON_TERMINAL
                DISPLAY.rotation = 0
                DISPLAY.refresh()
                raise exception


    def show_titles_only():
        Gui.__text_title.max_lines = Gui.__title_only_max_lines
        Gui.__text_title.positions = Gui.__title_only_positions
        Gui.__text_title.show()
        Gui.__text_sub_title.max_lines = Gui.__sub_title_only_max_lines
        Gui.__text_sub_title.positions = Gui.__sub_title_only_positions
        Gui.__text_sub_title.show()
        Gui.__text_turn_time.hide()
        Gui.__text_total_time.hide()
        DISPLAY.root_group = Gui.__root_main
        Gui.set_rotation(DISPLAY.rotation, force=True)

    def show_titles_and_times():
        Gui.__text_title.max_lines = Gui.__title_and_times_max_lines
        Gui.__text_title.positions = Gui.__title_and_times_positions
        Gui.__text_title.show()
        Gui.__text_sub_title.max_lines = Gui.__sub_title_and_times_max_lines
        Gui.__text_sub_title.positions = Gui.__sub_title_and_times_positions
        Gui.__text_sub_title.show()
        Gui.__text_turn_time.show()
        Gui.__text_total_time.show()
        DISPLAY.root_group = Gui.__root_main
        Gui.set_rotation(DISPLAY.rotation, force=True)

    # ============== SPLASH ===================

    def set_splash_text(text):
        debug(f"Splash: {text}")
        Gui.__splash_text.set_text(text)
        DISPLAY.refresh()

    # ============== IN GAME STUFF ===================

    def get_foreground(rgb_color=(0,128,255)):
        (r,g,b)=rgb_color
        hsp = sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        if (hsp>127.5):
            return (0,0,0)
        else:
            return (255,255,255)

    def set_background(bg_color, sandtimer_pos=-240):
        if (Gui.__bg_rect_sandtimer_group.y != sandtimer_pos):
            debug(f'Move sandtimer to {sandtimer_pos}')
            Gui.__bg_rect_sandtimer_group.y = sandtimer_pos
        if (Gui.__curr_bg_color != bg_color):
            Gui.__curr_bg_color = bg_color
            Gui.__bg_rect.fill = bg_color
            fg_color = Gui.get_foreground(bg_color)
            # The icons must always be redrawn whenever the background changes.
            for icon in Gui.__all_icons:
                icon.update_palette(bg_color, fg_color)
            if (Gui.__curr_fg_color != fg_color):
                Gui.__curr_fg_color = fg_color
                # The text color only need to update if the fg color changes
                for text in Gui.__all_texts:
                    text.set_color(fg_color)

    def update_sandtimer_position(percent_remaining):
        y_pos = int(-240 * percent_remaining)  # -240 = all time remaining -> 0 = no time remaining
        Gui.set_background(SAND_COLOR_TIME_LEFT, sandtimer_pos=y_pos)

    def set_title(title_text, sub_title_text=""):
        Gui.__text_title.set_text(title_text)
        sub = '({})'.format(sub_title_text) if sub_title_text else ""
        if sub == '(Admin Time)':
            sub = '(Admin)'
        Gui.__text_sub_title.set_text(sub)

    def set_turn_time(text):
        Gui.__text_turn_time.set_text(text)

    def set_total_time(text):
        Gui.__text_total_time.set_text(text)

    def set_battery(percentage):
        if percentage > 90:
            Gui.__icon_set_battery.show('100')
        elif percentage > 70:
            Gui.__icon_set_battery.show('80')
        elif percentage > 50:
            Gui.__icon_set_battery.show('60')
        elif percentage > 30:
            Gui.__icon_set_battery.show('40')
        elif percentage > 10:
            Gui.__icon_set_battery.show('20')
        else:
            Gui.__icon_set_battery.show('0')

    def set_syncing(is_syncing):
        if is_syncing:
            Gui.__icon_set_state.show("sync")
        else:
            Gui.__icon_set_state.show(None)

    def set_primary_action_icon(action_key):
        Gui.__icon_set_primary.show(action_key)
    def set_secondary_action_icon(action_key):
        Gui.__icon_set_secondary.show(action_key)
    def set_admin_action_icon(action_key):
        Gui.__icon_set_admin.show(action_key)

    # ============== HELPER METHODS ===================

    def __append_label(positions, fonts, max_text_widths, max_lines=(1,2,1,2), scales=(1,), allowed_glyphs=None):
        text = Text(positions=positions, max_text_widths=max_text_widths, fonts=fonts, max_lines=max_lines, scales=scales, allowed_glyphs=allowed_glyphs)
        Gui.__root_main.append(text.label)
        Gui.__all_texts.append(text)
        return text

    def __append_icon_set(paths, positions):
        from icon import IconSet
        iconSet = IconSet(paths, positions)
        for key, icon in iconSet.icons.items():
            Gui.__root_main.append(icon.tile_grid)
            Gui.__all_icons.append(icon)
        return iconSet

    def set_rotation(rotation, force=False):
        if force or DISPLAY.rotation != rotation:
            DISPLAY.rotation = rotation % 360
            rotation_index = int(DISPLAY.rotation / 90)
            if DISPLAY.root_group == Gui.__root_splash:
                Gui.__splash_text.set_rotation_index(rotation_index)
                hide_big = rotation_index == 0 or rotation_index == 2

                Gui.__splash_image_big.hidden = hide_big
                Gui.__splash_image_small.hidden = not hide_big
            else:
                for text in Gui.__all_texts:
                    text.set_rotation_index(rotation_index)
                for icon in Gui.__all_icons:
                    icon.set_rotation_index(rotation_index)

    def rotate():
        Gui.set_rotation((DISPLAY.rotation + 90) % 360)