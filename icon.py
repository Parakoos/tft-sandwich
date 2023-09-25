from displayio import Bitmap, Palette, TileGrid
from adafruit_imageload import load

GammaCorrection = 2.2

class Icon:
    def __init__(self, path, positions):
        self.positions = positions
        self.path = path
        image, palette = load(path, bitmap=Bitmap, palette=Palette)
        self.bitmap = image
        self.grayscale_palette = []
        self.palette = palette
        i = 0
        while True:
            try:
                RGBint = palette[i]
                b =  RGBint & 255
                g = (RGBint >> 8) & 255
                r =   (RGBint >> 16) & 255
                avg = int((r+g+b) / 3)
                self.grayscale_palette.append(avg/255)
                i = i + 1
            except Exception as err:
                break
        self.tile_grid = TileGrid(image, pixel_shader=self.palette)
        self.tile_grid.hidden = True
        self.set_rotation_index(0)

    def update_palette(self, background_color, foreground_color):
        for i in range(len(self.grayscale_palette)):
            opacity = self.grayscale_palette[i]
            self.palette[i] = (self.mix_colors(background_color[0], foreground_color[0], opacity),
                               self.mix_colors(background_color[1], foreground_color[1], opacity),
                               self.mix_colors(background_color[2], foreground_color[2], opacity))

    def mix_colors(self, background_color_part, foreground_color_part, opacity):
        color_part = (opacity * background_color_part) + ((1 - opacity) * foreground_color_part)
        return min(255, round(color_part))

    def show(self):
        self.tile_grid.hidden = False

    def hide(self):
        self.tile_grid.hidden = True

    def get_rotation_value(self, rotation_values):
        return rotation_values[self.current_rotation_index % len(rotation_values)]

    def set_rotation_index(self, index):
        self.current_rotation_index = index
        x, y = self.get_rotation_value(self.positions)
        self.tile_grid.x = x
        self.tile_grid.y = y

class IconSet:
    def __init__(self, paths, positions):
        self.positions = positions
        self.icons = {}
        for key, path in paths.items():
            icon = Icon(path, positions)
            self.icons[key] = icon

    def show(self, key):
        for _key, icon in self.icons.items():
            if key == _key:
                icon.show()
            else:
                icon.hide()