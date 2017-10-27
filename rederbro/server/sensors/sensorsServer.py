from rederbro.server.server import Server
from rederbro.utils.serialManager import SerialManager
import serial


class SensorsServer(Server):
    """
    A server who manage sensors :
                            --> gps
                            --> compas
    """

    def turnAutomode(self, state):
        """
        Turn automode on or off (state).

        Auto mode will take a picture every self.distace meter.
        """
        self.logger.info("Auto mode turned {}".format(state))

    def setDistance(self, distance):
        """
        Set distance between picture in auto mode.

        This method don't turn on auto mode.
        """
        self.distance = distance
        self.logger.info("Distance between photo set to {}".format(self.distance))

    def toDegCord(self):
        """
        Return latitude and longitude in degree.

        google earth and some other thing prefer degree coordinate.
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

    def getCoord(self):
        self.logger.info("Get coordonate")
        if self.fakeMode:
            self.lastCord = [0, 0, 0]
            self.logger.info("Coordonate : {} (fake mode)".format(self.lastCord))

        else:
            checkNB = int(self.time_out/0.5)

            for i in range(checkNB):
                error, answer = self.gps.waitAnswer("")
                answer = answer.split(",")
                if answer[0] == "$GPGGA":
                    error = False
                    break

            if not error:
                #$GPGGA,<time>,<lat>,<N/S>,<lon>,<E/W>,<positionnement type>,<satelite number>,<HDOP>,<alt>,<other thing>
                self.lastSat = answer[7]
                self.lastCord = [answer[2]+answer[3], answer[4]+answer[5], answer[9]]
                self.lastTime = answer[1]
                self.lastHdop = answer[8]

                self.toDegCord()

                self.logger.info("Current cordonate : {}".format(self.lastCord))

            else:
                self.lastCord = [0, 0, 0]
                self.logger.error("Failed to get new coordonate")

        return lastCord


    def __init__(self, config):
        Server.__init__(self, config, "sensors")

        self.lastSat = 0
        self.lastCord = [0, 0, 0]
        self.lastTime = 0
        self.lastHdop = 0

        self.command = {\
            "debug": (self.setDebug, True),\
            "fake": (self.setFakeMode, True),\
            "automode": (self.turnAutomode, True),\
            "distance": (self.setDistance, True),\
            "getCoord": (self.getCoord, False)\
        }

        self.distance = 5

        self.time_out = config["gps"]["time_out"]

        try:
            self.gps = SerialManager(self.config, self.logger, "gps")
        except:
            self.setFakeMode("on")
