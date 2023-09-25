from adafruit_display_text import label, wrap_text_to_lines
from debug import debug

class Text:
    def __init__(self, positions, max_text_widths, fonts, max_lines=(1,2,1,2), scales=(1,), line_spacing=0.7, allowed_glyphs=None):
        self.positions = positions
        self.max_text_widths = max_text_widths
        self.scales = scales
        self.fonts = fonts
        self.current_text = " "*max_text_widths[0]
        self.current_rotation_index = 0
        self.label = label.Label(fonts[0], text=self.current_text, color=0x000000, scale=scales[0], line_spacing=line_spacing)
        # self.label = bitmap_label.Label(fonts[0], text=self.current_text, color=0x000000, scale=scales[0], line_spacing=line_spacing)
        self.label.anchor_point = (0.5, 0)
        self.label.anchored_position = positions[0]
        self.max_lines = max_lines
        self.allowed_glyphs=allowed_glyphs
        # self.label.background_color=0x555555

    def show(self):
        self.label.hidden = False

    def hide(self):
        self.label.hidden = True

    def get_rotation_value(self, rotation_values):
        return rotation_values[self.current_rotation_index % len(rotation_values)]

    def set_text(self, text):
        self.current_text = text
        text_filtered = text if self.allowed_glyphs == None else ''.join([i for i in text if i in self.allowed_glyphs])
        max_lines = self.get_rotation_value(self.max_lines)
        wrapped_text = wrap_text(text_filtered, self.get_rotation_value(self.max_text_widths), font=self.get_rotation_value(self.fonts), max_lines=max_lines)
        self.label.text = wrapped_text

    def set_color(self, color):
        self.label.color = color

    def set_rotation_index(self, index):
        self.current_rotation_index = index
        self.label.anchored_position = self.get_rotation_value(self.positions)
        self.label.scale = self.get_rotation_value(self.scales)
        self.label.font = self.get_rotation_value(self.fonts)
        self.set_text(self.current_text)


def wrap_text(text, max_width, max_lines, font=None, indent0="", indent1=""):
    if font is None:
        def measure(s):
            return len(s)
    else:
        if hasattr(font, 'load_glyphs'):
            font.load_glyphs(text)
        def measure(s):
            return sum(font.get_glyph(ord(c)).shift_x for c in s)

    lines = []
    partial = [indent0]
    width = measure(indent0)
    swidth = measure(' ')
    firstword = True
    for word in text.split():
        wwidth = measure(word)
        if firstword:
            partial.append(word)
            firstword = False
            width += wwidth
        elif width + swidth + wwidth < max_width:
            partial.append(" ")
            partial.append(word)
            width += wwidth + swidth
        else:
            lines.append("".join(partial))
            partial = [indent1, word, ' ']
            width = measure(indent1) + wwidth + swidth
            firstword = True
    if partial:
        lines.append("".join(partial))

    lines = lines[:max_lines]

    if len(lines) == 2:
        while True:
            line_one_words = lines[0].split()
            if len(line_one_words) <= 1:
                break
            first, *middle, last = line_one_words

            if measure(lines[0])-measure(last)-swidth >= measure(lines[1])+measure(last)+swidth:
                lines[0] = "  ".join([first] + middle)
                lines[1] = f"{last} {lines[1]}"
            else:
                break

    return "\n".join(lines)