import time
class AHT20:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address
        time.sleep_ms(20)
        self.i2c.writeto(self.address, b'\xBE')  # soft reset
        time.sleep_ms(20)
        self._trigger_measure()

    def _trigger_measure(self):
        self.i2c.writeto(self.address, b'\xAC\x33\x00')
        time.sleep_ms(80)
        data = self.i2c.readfrom(self.address, 7)
        if data[0] & 0x80:
            raise Exception("AHT20 not ready")
        raw_temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        raw_hum = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        self._humidity = (raw_hum / (1 << 20)) * 100
        self._temperature = (raw_temp / (1 << 20)) * 200 - 50

    @property
    def temperature(self):
        self._trigger_measure()
        return self._temperature

    @property
    def relative_humidity(self):
        self._trigger_measure()
        return self._humidity
