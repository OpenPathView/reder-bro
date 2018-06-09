from threading import Thread
from rederbro.command.command import Command
import time
from math import radians, cos, sin, acos


class Automode(Thread):
    EARTH_RADIUS = 6367.445  # found on da internet m
    work = True

    def __init__(self, sensors, distance, config={}):
        self.sensors = sensors
        self.distance = distance
        self.config = config
        Thread.__init__(self)

    def run(self):
        self.lastCord = self.sensors.getSensors()
        self.takePic()

        while self.work:
            cord = self.sensors.getSensors(log=False)
            distance = self.getDistance(self.lastCord, cord)
            self.sensors.logger.debug("Distance : {}".format(distance))
            if distance >= self.distance:
                self.lastCord = cord
                self.sensors.logger.info("Ask a picture (automode)")
                self.takePic()
            time.sleep(0.2)

    def takePic(self):
        msg = ("takepic", True)
        cmd = Command(self.config, "gopro")
        cmd.run(msg)

    def setDistance(self, distance):
        self.distance = distance

    def getDistance(self, last, now):
        lastLat, lastLon = radians(last["lat"]), radians(last["lon"])
        newLat, newLon = radians(now["lat"]), radians(now["lon"])

        return 1000.0*self.EARTH_RADIUS*acos(sin(lastLat)*sin(newLat)+cos(lastLat)*cos(newLat)*cos(lastLon-newLon))

    def stop(self):
        self.work = False
