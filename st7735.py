# st7735.py - ST7735S/R driver for MicroPython
from time import sleep_ms
import framebuf

# ST7735 commands
_SWRESET = 0x01
_SLPOUT  = 0x11
_DISPON  = 0x29
_CASET   = 0x2A
_RASET   = 0x2B
_RAMWR   = 0x2C
_MADCTL  = 0x36
_COLMOD  = 0x3A
_INVON   = 0x21

class ST7735:
    def __init__(self, spi, width, height, cs, dc, reset=None, rotation=0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = reset
        self.width = width
        self.height = height
        self.rotation = rotation

        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        if self.rst:
            self.rst.init(self.rst.OUT, value=1)
        self.buffer = bytearray(self.height * self.width * 2)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)

        self.init()

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

    def hard_reset(self):
        if self.rst:
            self.rst(1)
            sleep_ms(50)
            self.rst(0)
            sleep_ms(50)
            self.rst(1)
            sleep_ms(150)

    def init(self):
        self.hard_reset()
        self.write_cmd(_SWRESET)
        sleep_ms(150)
        self.write_cmd(_SLPOUT)
        sleep_ms(500)

        self.write_cmd(_COLMOD)
        self.write_data(bytearray([0x05]))  # 16-bit color
        sleep_ms(10)

        self.write_cmd(_MADCTL)
        if self.rotation == 0:
            self.write_data(bytearray([0x00]))
        elif self.rotation == 1:
            self.write_data(bytearray([0x60]))
        elif self.rotation == 2:
            self.write_data(bytearray([0xC0]))
        elif self.rotation == 3:
            self.write_data(bytearray([0xA0]))

        self.write_cmd(_DISPON)
        sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(_CASET)
        self.write_data(bytearray([(x0 >> 8) & 0xFF, x0 & 0xFF, (x1 >> 8) & 0xFF, x1 & 0xFF]))
        self.write_cmd(_RASET)
        self.write_data(bytearray([(y0 >> 8) & 0xFF, y0 & 0xFF, (y1 >> 8) & 0xFF, y1 & 0xFF]))
        self.write_cmd(_RAMWR)

    def fill(self, color):
        c = color.to_bytes(2, 'big')
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.cs(0)
        self.dc(1)
        self.spi.write(c * self.width * self.height)
        self.cs(1)

    def pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.set_window(x, y, x, y)
            self.write_data(color.to_bytes(2, 'big'))

    def text(self, font, text, x, y, color):
        self.framebuf.fill(0)
        self.framebuf.text(text, 0, 0, color)
        for row in range(8):
            for col in range(len(text) * 8):
                p = self.framebuf.pixel(col, row)
                if p:
                    self.pixel(x + col, y + row, color)

    def blit_buffer(self, buf, x, y, w, h):
        self.set_window(x, y, x + w - 1, y + h - 1)
        self.cs(0)
        self.dc(1)
        self.spi.write(buf)
        self.cs(1)

    @staticmethod
    def color565(r, g, b):
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
