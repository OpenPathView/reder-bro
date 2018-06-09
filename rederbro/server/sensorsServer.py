from rederbro.server.worker import Worker
from rederbro.utils.serialManager import SerialManager
from rederbro.utils.automode import Automode
import zmq
import Adafruit_ADS1x15


class SensorsServer(Worker):
    """
    A server who manage sensors :
                            --> gps
                            --> compas
                            --> voltmeter
    """

    def turnAutomode(self, state):
        """
        Turn automode on or off (state).

        Auto mode will take a picture every self.distace meter.
        """
        self.logger.info("Lets turn automode {}".format(state))
        self.automode.stop()
        if (state == "on"):
            self.automode = Automode(self, self.distance, config=self.config)
            self.automode.start()

        self.logger.info("Auto mode turned {}".format(state))

    def setDistance(self, distance):
        """
        Set distance between picture in auto mode.

        This method don't turn auto mode on.
        """
        self.distance = float(distance)
        self.automode.setDistance(distance)
        self.logger.info("Distance between photo set to {}".format(self.distance))

    def toDegCord(self):
        """
        Return latitude and longitude in degree.

        google earth and some other thing prefer degree cordinate.
        """
        lat = self.lastCord[0]
        lon = self.lastCord[1]
        # ensure that we have data to work with
        if lat is not None and lon is not None and len(lat) > 0 and len(lon) > 0:
            try:
                if lat[-1] == "N":  # define the signe
                    lat = float(lat[:-1])/100.0
                else:
                    lat = -float(lat[:-1])/100.0

                if lon[-1] == "W":  # define the signe
                    lon = -float(lon[:-1])/100.0
                else:
                    lon = float(lon[:-1])/100.0
            except (TypeError, ValueError):
                return None, None
            lat_deg = int(lat)
            lat_min = (100.0*(float(lat)-lat_deg))/60
            lat = lat_deg+lat_min

            lon_deg = int(lon)
            lon_min = (100.0*(float(lon)-lon_deg))/60
            lon = lon_deg+lon_min

            self.lastCord[0] = lat
            self.lastCord[1] = lon
            return self.lastCord

        return 0, 0  # mean it didin't work

    def getHeading(self):
        self.heading = 0.0
        return self.heading

    def getVoltage(self, log=True):
        """Retriev the battery voltage."""
        if log:
            self.logger.info("Get battery voltage")
        if self.fakeMode:
            self.battVoltage = 42
            if log:
                self.logger.info("Battery voltage : {} (fake mode)"
                                 .format(self.battVoltage))
        else:
            # G = 1 = +/-4.096V
            GAIN = 1
            # Because Voltage divider in inpout
            self.value = self.adc.read_adc(0, gain=GAIN)
            battery_voltage_low = (self.value * 4.096) / 32767.0
            self.battVoltage = round((battery_voltage_low * 3.2), 2)
            if log:
                self.logger.info("Battery voltage : {}".format(self.battVoltage))

        return self.battVoltage

    def getSensors(self, log=True):
        if log:
            self.logger.info("Get coordinates")
        if self.fakeMode:
            self.lastCord = [0.0, 0.0, 0.0]
            self.lastSat = 0
            self.lastTime = 0.0
            self.lastHdop = 0
            if log:
                self.logger.info("coordinates : {} (fake mode)".format(self.lastCord))

        else:
            checkNB = int(self.time_out/0.5)

            for i in range(checkNB):
                error, answer = self.gps.waitAnswer("")
                answer = answer.split(",")
                if answer[0] == "$GPGGA":
                    error = False
                    break

            if not error:
                # $GPGGA,<time>,<lat>,<N/S>,<lon>,<E/W>,<positionnement type>,<satelite number>,<HDOP>,<alt>,<other thing>
                self.lastSat = answer[7]
                self.lastCord = [answer[2]+answer[3], answer[4]+answer[5], float(answer[9])]
                self.lastTime = float(answer[1])
                self.lastHdop = answer[8]

                self.toDegCord()

                if log:
                    self.logger.info("Current coordinates : {}".format(self.lastCord))

            else:
                self.lastCord = [0, 0, 0]
                self.logger.error("Failed to get new coordinates")

        sensorsJson = {"lat": self.lastCord[0],
                       "lon": self.lastCord[1],
                       "alt": self.lastCord[2],
                       "head": self.getHeading(),
                       "battVoltage": self.getVoltage(),
                       "time": self.lastTime}
        self.gps_infoPub.send_json(sensorsJson)
        self.logger.debug("Data return from get cord : {}".format(sensorsJson))

        return sensorsJson

    def pollCall(self, poll):
        """If other socket is call get there."""
        if self.gps_infoRep in poll:
            self.gps_infoRep.recv_json()
            rep = self.getSensors()
            self.gps_infoRep.send_json(rep)

    def __init__(self, config):
        Worker.__init__(self, config, "sensors")

        self.lastSat = 0
        self.lastCord = [0.0, 0.0, 0.0]
        self.lastTime = 0.0
        self.lastHdop = 0.0
        self.heading = 0.0
        self.battVoltage = 0.0

        self.earth_radius = 6372.795477598 * 1000

        self.command = {
            "debug": (self.setDebug, True),
            "fake": (self.setFakeMode, True),
            "automode": (self.turnAutomode, True),
            "distance": (self.setDistance, True),
            "get": (self.getSensors, False)
        }

        urlGPS = "tcp://{}:{}".format(self.config["gps"]["bind_url"], self.config["gps"]["pub_server_port"])
        self.gps_infoPub = self.context.socket(zmq.PUB)
        self.gps_infoPub.bind(urlGPS)

        urlGPS2 = "tcp://{}:{}".format(self.config["gps"]["bind_url"], self.config["gps"]["rep_server_port"])
        self.gps_infoRep = self.context.socket(zmq.REP)
        self.gps_infoRep.bind(urlGPS2)

        self.poller.register(self.gps_infoRep, zmq.POLLIN)

        self.time_out = config["gps"]["time_out"]

        try:
            self.gps = SerialManager(self.config, self.logger, "gps")
        except Exception as e:
            self.logger.info("Can't connect to gps ({})".format(e))
            self.setFakeMode("on")

        try:
            self.adc = Adafruit_ADS1x15.ADS1115()
        except Exception as e:
            self.logger.info("Error Initializing battery voltmeter {}".format(e))
            self.setFakeMode("on")

        self.distance = 5
        self.automode = Automode(self, self.distance, config=self.config)
