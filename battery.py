
import time
import color
import threading
import Adafruit_ADS1x15


class Battery(threading.Thread):
    """A simple class to acces the battery voltage."""

    def __init__(self, opvServer=None):
        """Init all stuff."""
        print(color.OKBLUE + "Initializing Battery thread...", color.ENDC)
        self.batteryThread = None
        self.battery_voltage = 0
        self.value = 0
        try:
            self.adc = Adafruit_ADS1x15.ADS1115()
        except Exception:
            print("Error Initializing battery voltmeter")
        self.__dataLoop = True
        self.batteryThread = threading.Thread(target=self.fetchBatteryVoltage)
        self.batteryThread.daemon = True
        self.batteryThread.start()

    def fetchBatteryVoltage(self):
        """Return the battery voltage."""
        # G = 1 = +/-4.096V
        GAIN = 1
        # Because Voltage divider in inpout
        while self.__dataLoop:
            self.value = self.adc.read_adc(0, gain=GAIN)
            battery_voltage_low = (self.value * 4.096) / 32767.0
            self.battery_voltage = round((battery_voltage_low * 3.2), 2)
            time.sleep(10)

    def getBatteryVoltage(self):
        return self.battery_voltage


if __name__ == "__main__":
    battery = Battery()
