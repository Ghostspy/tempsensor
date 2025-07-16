import time
import struct

class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        self._load_calibration()
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')  # normal mode
        self.i2c.writeto_mem(self.addr, 0xF5, b'\xA0')  # config

    def _read16(self, reg):
        d = self.i2c.readfrom_mem(self.addr, reg, 2)
        return d[1] << 8 | d[0]

    def _read16s(self, reg):
        result = self._read16(reg)
        if result > 32767:
            result -= 65536
        return result

    def _read24(self, reg):
        d = self.i2c.readfrom_mem(self.addr, reg, 3)
        return (d[0] << 16) | (d[1] << 8) | d[2]

    def _load_calibration(self):
        calib = self.i2c.readfrom_mem(self.addr, 0x88, 24)
        self.dig_T1 = struct.unpack_from("<H", calib, 0)[0]
        self.dig_T2 = struct.unpack_from("<h", calib, 2)[0]
        self.dig_T3 = struct.unpack_from("<h", calib, 4)[0]
        self.dig_P1 = struct.unpack_from("<H", calib, 6)[0]
        self.dig_P2 = struct.unpack_from("<h", calib, 8)[0]
        self.dig_P3 = struct.unpack_from("<h", calib, 10)[0]
        self.dig_P4 = struct.unpack_from("<h", calib, 12)[0]
        self.dig_P5 = struct.unpack_from("<h", calib, 14)[0]
        self.dig_P6 = struct.unpack_from("<h", calib, 16)[0]
        self.dig_P7 = struct.unpack_from("<h", calib, 18)[0]
        self.dig_P8 = struct.unpack_from("<h", calib, 20)[0]
        self.dig_P9 = struct.unpack_from("<h", calib, 22)[0]

    def _read_raw_data(self):
        data = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return adc_t, adc_p

    def read_compensated_data(self):
        adc_t, adc_p = self._read_raw_data()

        # Temperature compensation
        var1 = ((((adc_t >> 3) - (self.dig_T1 << 1))) * self.dig_T2) >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        temp = (t_fine * 5 + 128) >> 8

        # Pressure compensation
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33

        if var1 == 0:
            pressure = 0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)

        return temp / 100.0, pressure / 256.0

    @property
    def temperature(self):
        t, _ = self.read_compensated_data()
        return t

    @property
    def pressure(self):
        _, p = self.read_compensated_data()
        return p
