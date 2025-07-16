from time import sleep_ms
import framebuf

class ST7735S:
    def __init__(self, spi, cs, dc, reset, width=128, height=128, rotation=0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.reset = reset
        self.width = width
        self.height = height
        self.rotation = rotation

        self.x_offset = 2
        self.y_offset = 1

        self.buffer = bytearray(self.width * self.height * 2)
        self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)

        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.reset.init(self.reset.OUT, value=1)

        self.init_display()

    def write_cmd(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.cs(0)
        self.dc(1)
        self.spi.write(data)
        self.cs(1)

    def init_display(self):
        self.reset(1)
        sleep_ms(50)
        self.reset(0)
        sleep_ms(50)
        self.reset(1)
        sleep_ms(150)

        self.write_cmd(0x01)  # SWRESET
        sleep_ms(150)
        self.write_cmd(0x11)  # SLPOUT
        sleep_ms(255)
        self.write_cmd(0x3A)  # COLMOD
        self.write_data(bytearray([0x05]))  # 16-bit color
        self.write_cmd(0x36)  # MADCTL
        self.write_data(bytearray([0xC8]))  # RGB, row/col order
        self.write_cmd(0x29)  # DISPON
        sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        x0 += self.x_offset
        x1 += self.x_offset
        y0 += self.y_offset
        y1 += self.y_offset

        self.write_cmd(0x2A)
        self.write_data(bytearray([0, x0, 0, x1]))
        self.write_cmd(0x2B)
        self.write_data(bytearray([0, y0, 0, y1]))
        self.write_cmd(0x2C)

    def fill(self, color):
        self.set_window(0, 0, self.width - 1, self.height - 1)
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        self.cs(0)
        self.dc(1)
        self.spi.write(bytes([hi, lo]) * self.width * self.height)
        self.cs(1)

    def color565(self, r, g, b):
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    def pixel(self, x, y, color):
        self.set_window(x, y, x, y)
        self.write_data(color.to_bytes(2, 'big'))

    def text(self, font, text, x, y, color):
        for i, c in enumerate(text):
            char_code = ord(c)
            if 32 <= char_code <= 127:
                char_code -= 32  # offset because font starts at space (32)
                for row in range(8):
                    line = font[char_code * 8 + row]
                    for col in range(8):
                        if line & (0x80 >> col):
                            self.pixel(x + i * 8 + col, y + row, color)
            else:
                # skip unknown chars
                pass
