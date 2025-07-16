from machine import I2C, Pin, SPI, Timer
import time
import framebuf
from ahtx0 import AHT20
from bmp280 import BMP280
import st7735
import vga1_8x8 as font
from st7735 import ST7735

# === I2C Setup ===
i2c = I2C(0, scl=Pin(6), sda=Pin(5))

# === Sensor Init ===
aht = AHT20(i2c)

# Try both BMP280 addresses
bmp = None
for addr in (0x76, 0x77):
    try:
        bmp = BMP280(i2c, addr=addr)
        print("BMP280 found at 0x{:02X}".format(addr))
        break
    except OSError:
        pass

# === SPI Display Setup ===
spi = SPI(1, baudrate=20000000, sck=Pin(7), mosi=Pin(9))
dc = Pin(3)
cs = Pin(2)
rst = Pin(4)
tft = st7735.ST7735(spi, 128, 128, cs=cs, dc=dc, reset=rst, rotation=2)
tft.init()

# === UI Colors ===
RED = ST7735.color565(0, 0, 255)
GREEN = ST7735.color565(0, 255, 0)
BLUE = ST7735.color565(153, 0, 0)
WHITE = ST7735.color565(255, 255, 255)
YELLOW = ST7735.color565(0, 255, 255)

# === Load Background ===
def draw_background():
    try:
        with open("bg.raw", "rb") as f:
            # Read the whole image (128x128 RGB565 = 32768 bytes)
            buf = f.read(128 * 128 * 2)
            tft.blit_buffer(buf, 0, 0, 128, 128)
    except Exception as e:
        print("Error drawing bg.raw:", e)

# === Dim & Wake Logic ===
DIM_TIMEOUT = 120  # seconds
dimmed = False
last_active = time.time()
wake_button = Pin(1, Pin.IN, Pin.PULL_UP)

def dim_display():
    global dimmed
    tft.fill(0)
    dimmed = True
    print("Display dimmed.")

def wake_display(pin=None):
    global dimmed, last_active
    last_active = time.time()
    if dimmed:
        draw_background()
        show_current_data()
        dimmed = False
        print("Display woken.")

wake_button.irq(trigger=Pin.IRQ_FALLING, handler=wake_display)

# === Sensor Display Function ===
def show_current_data():
    try:
        temp_c = aht.temperature
        hum = aht.relative_humidity
        temp_f = temp_c * 9 / 5 + 32
    except Exception as e:
        print("AHT20 error:", e)
        temp_f = hum = None

    try:
        pressure_hpa = bmp.pressure if bmp else None
        pressure_inhg = pressure_hpa * 0.02953 if pressure_hpa else None
    except Exception as e:
        print("BMP280 error:", e)
        pressure_inhg = None

    tft.text(font, "Temp Sensor 1", 10, 5, WHITE)

    if temp_f is not None:
        tft.text(font, "Temp:{:.1f}F".format(temp_f), 10, 25, WHITE)
    else:
        tft.text(font, "Temp: ---", 10, 25, RED)

    if hum is not None:
        tft.text(font, "Hum :{:.1f}%".format(hum), 10, 35, WHITE)
    else:
        tft.text(font, "Hum : ---", 10, 35, RED)

    if pressure_inhg is not None:
        tft.text(font, "Pres:{:.2f}inHg".format(pressure_inhg), 10, 45, WHITE)
    else:
        tft.text(font, "Pres: ---", 10, 45, RED)

# === Main Loop ===
def show_data():
    global last_active, dimmed

    while True:
        now = time.time()

        if not dimmed:
            draw_background()
            show_current_data()

        if not dimmed and now - last_active > DIM_TIMEOUT:
            dim_display()

        time.sleep(60)

# === Start ===
wake_display()  # Show first frame
show_data()
