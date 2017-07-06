#Software under Creative Commons Licences By-Nc-Sa 3.0
#Read the licence.txt file for further information
import serial, time, math
import threading, os
from math import radians,cos,sin,acos,asin
import color

END = b"\r\n"
DIST_TRIGGER = 10
EARTH_RADIUS = 6367.445 #found on da internet m


class Gps(object):
    """
    a class to manage serial connected gps
    """

    def __init__(self,opvServer=None,port=None, baudrate=115200, timeout=1):
        """
        init the gps, if all needed information are provided, will connect the serial
        """
        print(color.OKBLUE+"Initializing GPS...",color.ENDC)
        assert type(baudrate) is int
        assert type(timeout) in (float,int)
        assert (type(port) in (str,int) or port == None)

        self.opvServer=opvServer
        self.sat = None
        self.lat = None
        self.lon = None
        self.dDistance = None
        self.last_coord = [0,0]
        self.last_time = None
        self.dTime = None
        self.alt = None
        self.time = None
        self.hdop = None
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.readTimeout = 1
        self.data = None
        self.__updateThread = None
        if port!=None and not self.opvServer.config.get("FAKE_MODE"):
            self.connect()
        else:
            self.ser = None
        self.__dataLoop = True
        print(color.OKGREEN+"GPS initialized",color.ENDC)
        if self.opvServer.config.get("FAKE_MODE"):
            self.__updateData()

    def __del__(self):#ensure that the serial port is closed
        """
        destroy the gps
        """
        print(color.WARNING+"destroying GPS",color.ENDC)
        if self.ser != None:
            if self.ser.isOpen():
                self.ser.close()

    def connect(self):
        """
        connect the gps
        """

        if self.opvServer.config.get("FAKE_MODE"):
            return
        try:
                print("baudrate",self.baudrate)
                self.ser = serial.Serial(port=self.port,
                                         baudrate=self.baudrate,
                                         timeout=self.timeout)
        except ValueError as e: #Exeptions defined in pySerial
            print("Error",e)
            self.ser = None
        except serial.SerialException as e:
            print("Error",e)
            self.ser = None
        self.__dataLoop = True
        self.__updateThread = threading.Thread(target=self.__updateData)
        self.__updateThread.daemon = True
        self.__updateThread.start()

    def isConnected(self):
        """
        check if the gps is connected
        """

        if self.opvServer.config.get("FAKE_MODE"):#check if the GPS is connected
            return True
        elif self.ser != None:
            return self.ser.isOpen() and self.__dataLoop

    def disconnect(self):#close the serial port
        """
        disconnect the gps
        """

        if self.ser != None and not self.opvServer.config.get("FAKE_MODE"):
            self.__dataLoop = False
            self.ser.close()

    def stop(self):
        """
        stop the thread
        """
        print(color.OKBLUE+"Stopping GPS Thread...",color.ENDC)
        self.__dataLoop = False
        print(color.OKGREEN+"GPS Thread stopped",color.ENDC)

    def __updateData(self):
        """
        a loop to update data
        """

        if self.opvServer.config.get("FAKE_MODE"):
            self.sat = 7
            self.lat = "4821.5588333N"
            self.lon = "434.1788333W"
            self.last_coord = list(self.getDegCoord())

            self.alt = 0
            self.time = 1200.0
            self.hdop = 42
            self.dDistance = 0.1
            self.dTime = 0.1
            self.data = ""
            print(color.WARNING+"Warning : GPS in debug mode /!\\",color.ENDC)
            return 1

        if self.ser == None:
            print("No serial port declared")
            return -1

        if not self.isConnected():
            print("Serial port not connected")
            return -1
        else:
            msg = b""
            data = ""
            while self.__dataLoop :
                msg+=(self.ser.read(self.ser.inWaiting()))
                if END in msg:
                    try:
                        data=msg[:msg.find(END)].decode("ascii")
                    except UnicodeDecodeError:
                        data = ""
                    msg=msg[msg.find(END)+len(END):]
                    #os.system("echo '{0}' >> track_full".format(data))
                    data = data.split(",")

                    if data[0] == "$GPGGA":
                        with open("log.txt","a") as f:
                            f.writelines(str(data)+"\n")
                        if self.opvServer.config.get("GPS_DEBUG"):
                            print(data)
                        #$GGA,<time>,<lat>,<N/S>,<long>,<E/W>,<GPS-QUAL>,<satelite>,<hdop>,<alt>,<mode>,<otherthing>
                        self.sat = data[7]
                        self.lat = (data[2]+data[3])
                        self.lon = (data[4]+data[5])
                        self.alt = data[9]
                        self.time = data[1]
                        self.hdop = data[8]

                        lat,lon = self.last_coord
                        distance = self.calculateDist(lat,lon)
                        if distance >= DIST_TRIGGER:
                            self.last_coord = self.getDegCoord()
                            os.system("""echo "%f; %f" >> track"""%(self.last_coord[0],self.last_coord[1]))


                    if data[0]=="$GNGGA" and len(data) >= 10:#If the object contain the right data
                        if self.opvServer.config.get("GPS_DEBUG"):
                            print(data)
                        #$GPGGA,<time>,<lat>,<N/S>,<lon>,<E/W>,<positionnement type>,<satelite number>,<HDOP>,<alt>,<other thing>
                        self.data = data
                        self.sat = self.data[7]
                        self.lat = str(self.data[2]+self.data[3])
                        self.lon = str(self.data[4]+self.data[5])
                        self.alt = self.data[9]
                        self.time = self.data[1]
                        self.hdop = self.data[8]

                        lat,lon = self.last_coord
                        distance = self.calculateDist(lat,lon)
                        if distance >= DIST_TRIGGER:
                            self.last_coord = self.getDegCoord()
                            os.system("""echo "%f; %f" >> track"""%(self.last_coord[0],self.last_coord[1]))

    def getDataDict(self):
        """
        return all gps data under a dict structure
        """
        return {"sat":self.sat,
        "lat":self.lat,
        "lon":self.lon,
        "dDist":self.dDistance,
        "dTime":self.dTime,
        "alt":self.alt,
        "time":self.time,
        "hdop":self.hdop}

    def getDegCoord(self):#google earth and some other thing prefer degree coordinate
        """
        return latitude and longitude in degree
        """
        lat = self.lat
        lon = self.lon
        if lat !=None and lon != None and len(lat)>0 and len(lon)>0:#ensure that we have data to work with
            try :
                if lat[-1]=="N":#define the signe
                    lat = float(lat[:-1])/100.0
                else:
                    lat = -float(lat[:-1])/100.0

                if lon[-1]=="W":#define the signe
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

            return lat, lon

        return 0, 0#mean it didin't work

    def getAltitude(self):
        """
        return well formed altitude
        """
        if self.alt != None:
            try:
                return float(self.alt)
            except ValueError:
                return 0
        return 0

    def calculateDist(self,lastLat,lastLon):
        """
        return the distance from actual position
        """
        lastLat, lastLon = float(lastLat), float(lastLon)
        lastLat, lastLon = radians(lastLat), radians(lastLon)

        newLat, newLon = self.getDegCoord()
        if None in (newLat, newLon):
            return None
        newLat, newLon = float(newLat),float(newLon)
        newLat, newLon = radians(newLat), radians(newLon)
        try:
            return 1000.0*EARTH_RADIUS*acos(sin(lastLat)*sin(newLat)+cos(lastLat)*cos(newLat)*cos(lastLon-newLon))
        except ValueError:
            return 0


class gpsError(Exception):
    """
    exception raised when a probleme ocure with gps
    """
    def __init__(self, message, Errors):
        Exception.__init__(self, message)

        self.Errors = Errors
    def __str__(self):
        print("GPS ERROR : ",self.Errors)
