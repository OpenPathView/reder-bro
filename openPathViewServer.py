#!/usr/bin/python3.2

import RPi.GPIO as gpio

import os
import sys
import json
import time
import battery
import threading

sys.path.append(os.path.realpath(__file__)[:os.path.realpath(__file__).rfind("/")]+"/includes")
sys.path.append(os.path.realpath(__file__)[:os.path.realpath(__file__).rfind("/")]+"/includes/quick2wire-python-api/")

import gps, goPro, compas, color, config
from plugins import Manager

socketport=9876
EARTH_RADIUS = 6367.445 #found on da internet m


class OpenPathViewServer(threading.Thread):
    """
    main class of the project, manage the whole thing
    """

    def __init__(self):
        """
        init the server
        """
        print(color.OKBLUE+"Initializing main server...",color.ENDC)
        threading.Thread.__init__(self)
        self.keepAlive = threading.Event()
        self.keepAlive.set()
        self.config = config.Config()

        if not os.path.isfile("picturesInfo.csv"):
            os.system("""echo "time; lat; lon; alt; rad; goProFailed" >> picturesInfo.csv""")

        if not os.path.isfile("picturesInfo_secondaryGPS.csv"):
            os.system("""echo "time; lat; lon; alt; rad; goProFailed" >> picturesInfo_secondaryGPS.csv""")


        self.autoMode = threading.Event()
        self.distPhoto = 5
        self.configAutoModeLock = threading.Lock()

        self.configOnOffLock = threading.Lock()

        self.gps_secondary = gps.Gps(self, "/dev/ttyAMA0", baudrate=115200, trackfull_path="track_full_secondary",debug=False)
        self.gps = gps.Gps(self, self.config.get("MAIN_GPS_SERIAL"), baudrate=115200, trackfull_path="track_full_main",debug=False)
        self.lastLatLon = self.gps.getDegCoord()
        self.lastLatLon_secondary = self.gps_secondary.getDegCoord()

        self.compas = compas.Compas(self)
        self.gopro = goPro.GoPro(self)
        self.battery = battery.Battery(self)

        self.interfaces = Manager(self)

        self.geoInfoUpdateThread = threading.Thread(target = self.sendGeoInfoUpdateThread)
        self.geoInfoUpdateThread.daemon = True
        self.geoInfoUpdateThread.start()

        print(color.OKGREEN+"Main server initialized",color.ENDC)


    def isAutoMode(self):
        """
        return True if autoMode is enabled
        """
        return self.autoMode.isSet()

    def takePic(self):
        """
        take a pictures
        """
        print(color.OKBLUE+"Taking picture",color.ENDC)
        if not self.gps.isConnected():
            raise gps.gpsError("gps not connected")

        self.gopro.takePhoto()

    # def rafale(self):
    #     """
    #     Takes 10 pictures, only for test purposes.
    #     """
    #     self.gopro.rafale()

    def __turnOnThread(self):
        """
        the Thread that turn the GoPro on
        """
        print(color.OKBLUE+"Turning GoPro on",color.ENDC)
        if self.configOnOffLock.acquire(blocking=False):#if the Lock is unlocked
            if self.gopro.turnOn():
                self.interfaces.notif(True)
            else:
                self.interfaces.notif(False)
            self.configOnOffLock.release()
            return
        else:
            return

    def __turnOffThread(self):
        """
        the Thread that turn the GoPro off
        """
        print(color.OKBLUE+"Turning GoPro off",color.ENDC)
        if self.configOnOffLock.acquire(blocking=False):#if the Lock is unlocked
            if self.gopro.turnOff():
                self.interfaces.notif(True)
            else:
                self.interfaces.notif(False)
            self.configOnOffLock.release()
        else:
            return

    def turnOn(self):
        """
        turn all GoPro On
        """
        thread = threading.Thread(target = self.__turnOnThread)
        thread.daemon=True
        thread.start()


    def turnOff(self):
        """
        turn all GoPro Off
        """
        thread = threading.Thread(target = self.__turnOffThread)
        thread.daemon=True
        thread.start()

    def goproPowerOn(self):
        """
        Power all GoPro On
        """
        gpio.output(26, gpio.HIGH)

    def goproPowerOff(self):
        """
        Power all GoPro Off
        """
        gpio.output(26, gpio.LOW)

    def statut(self,succes,goProFailed="000000"):
        """
        act depending of the succes of photo taking
        goProFailed give the list of goPro wich failed to take a picture
        0 means no fail, the left one is goPro6 and the right is goPro1
        """
        rad = self.compas.getHeading()
        lat,lon = self.gps.getDegCoord()
        lat_secondary, lon_secondary = self.gps_secondary.getDegCoord()
        alt = self.gps.getAltitude()
        alt_secondary = self.gps_secondary.getAltitude()
        if succes:
            self.interfaces.newPanorama(True,latitude=lat,longitude=lon,altitude=alt,heading=rad)
        else:
            self.interfaces.newPanorama(False,goProFailed = goProFailed)

        os.system("""echo "{}; {:f}; {:f}; {:f}; {}; {}" >> picturesInfo.csv""".format(time.asctime(), lat, lon, alt, rad, goProFailed))
        os.system("""echo "{}; {:f}; {:f}; {:f}; {}; {}" >> picturesInfo_secondaryGPS.csv""".format(time.asctime(), lat_secondary, lon_secondary, alt_secondary, rad, goProFailed))

    def canMove(self):
        """
        tell all the interfaces the user can move
        """
        self.interfaces.canMove()

    def __automodeThread(self):
        """
        a thread taking picture when autoMode is set
        """
        print(color.OKBLUE+"starting autoMode"+color.ENDC)
        if not self.autoMode.isSet():
            self.autoMode.set()
            while self.autoMode.isSet() and self.keepAlive.isSet():
                lat, lon = self.lastLatLon
                distance = self.gps.calculateDist(lat,lon)
                if distance != None:
                    if distance>=self.distPhoto:
                        lastLatLon=self.gps.getDegCoord()
                        if not None in lastLatLon:
                            self.takePic()
                            self.lastLatLon = lastLatLon

            print(color.OKBLUE+"stoping autoMode"+color.ENDC)
        else:
            print(color.WARNING+"Error : autoMode already set"+color.ENDC)

    def run(self):
        """
        control thread : display information and allow command in the same time
        """
        while self.keepAlive.isSet():
            time.sleep(1)


    def setAuto(self,frequMetre=None):
        """
        set auto mode parameters, None mean Off
        """
        self.configAutoModeLock.acquire()
        if frequMetre:
            print("Setting auto mode for",frequMetre,"metres")
            self.distPhoto = frequMetre
            if not self.autoMode.isSet():
                automodeThread = threading.Thread(target=self.__automodeThread)
                automodeThread.daemon=True
                automodeThread.start()
        else:
            print("Disabling automode")
            self.autoMode.clear()
        self.configAutoModeLock.release()

    def socketHandler(self,socketSource,msg):
        """
        will be called by socket when they receiving a message
        """

        try:
            msg = json.loads(msg)
        except ValueError:
            print(color.FAIL, "Error decoding json from socket", color.ENDC)
            return

        if "action" in msg:
            if msg["action"]=="takepic":
                self.takePic()
            elif msg["action"]=="turnon":
                self.turnOn()
            elif msg["action"]=="turnoff":
                self.turnOff()
            elif msg["action"]=="gopropoweron":
                self.goproPowerOn()
            elif msg["action"]=="gopropoweroff":
                self.goproPowerOff()
            # elif msg["rafale"]=="rafale":
            #     self.rafale()
            else:
                print(color.WARNING,"WARNING : no correct action found in socket json",color.ENDC)
        if "set" in msg:
            if msg["set"]=="automode":
                try:
                    if msg["dist"]:
                        self.setAuto(int(msg["dist"]))
                    else:
                        self.setAuto()
                except KeyError:
                    print(color.FAIL,"Error : automode configuration fail",color.ENDC)
            else:
                print(color.WARNING,"WARNING : no correct setting field found in socket json",color.ENDC)

    def sendGeoInfoUpdateThread(self):
        """
        keep interfaces up to date with geolocalisation info
        """
        while self.keepAlive.isSet():
            lat,lon,alt,rad = self.getLatLonAltRad()
            battery_volatge = self.battery.getBatteryVoltage()
            self.interfaces.setGeoInfo(lat,lon,alt,rad)
            self.interfaces.setBatteryInfo(battery_volatge)
            time.sleep(0.05)

    def getLatLonAltRad(self):
        """
        return latitude, longitude and heading in degree
        """
        lat, lon = self.gps.getDegCoord()
        alt = self.gps.getAltitude()
        return lat,lon,alt,self.compas.getHeading().replace("°"," deg")

    def updateAllConfigInfo(self):
        """
        send config info to all connected devices
        """
        self.interfaces.setModeInfo(self.isAutoMode(),self.distPhoto)

    def stop(self):
        """
        stop all subThread
        """
        print(color.OKBLUE+"Stopping server...",color.ENDC)
        self.gps.stop()
        self.gps_secondary.stop()
        self.gopro.stop()
        self.interfaces.stop()
        self.keepAlive.clear()
        print(color.OKGREEN+"Server stopped",color.ENDC)

    def __del__(self):
        """
        destroyed need object
        """
        print(color.WARNING+"Destroying server and its component...",color.ENDC)
        for interface in self.interfaces:
            interface.__del__()
        self.gps.__del__()
        self.gps_secondary.__del__()
        self.gopro.__del__()
        print(color.WARNING+"Server destroyed",color.ENDC)

if __name__ == "__main__":
    os.system("clear")
    # GPIO Test (Quentin)
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    gpio.setup(26, gpio.OUT)

    server=OpenPathViewServer()
    try:
        server.start()
        server.join()
    except KeyboardInterrupt:
        print("""Ctrl-C detected, you could have typed "stop",it would be less brutal...""")
        os.system("reset")
        # curses.endwin()
    finally:
        server.stop()
        server.__del__()
