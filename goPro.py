import serial
import time
import threading
import subprocess
import color

ARDUINO_SERIAL = "/dev/ttyUSB0"

EYEFI_IP = ["192.168.42."+str(i) for i in range(100,106)]
#EYEFI_IP = ['192.168.42.100', '192.168.42.101', '192.168.42.102', '192.168.42.103', '192.168.42.104', '192.168.42.105']

class GoPro(threading.Thread):
    """
    that class allow the user to take photo via goPro camera
    """

    def __init__(self,osvServer = None, debug=False):
        """
        init serial port
        """
        print(color.OKBLUE+"Initializing GoPro server...",color.ENDC)
        threading.Thread.__init__(self)
        self.daemon = True
        self.debug = debug

        if not self.debug:
            self.arduino = serial.Serial(ARDUINO_SERIAL)
            self.arduino.readline()
        else:
            self.arduino = None
        
        self.takePhotoNow = threading.Event()
        
        self.arduinoReady = threading.Event()
        self.arduinoReady.set()
        
        self.osvServer = osvServer
        self.keepAlive = threading.Event()

        self.start()
        print(color.OKGREEN+"GoPro server initialized",color.ENDC)

            
    def __del__(self):
        """
        destructor
        """
        print(color.WARNING+"destroying GoPro",color.ENDC)

    def turnOn(self):
        """
        turn all GoPro on
        """
        if self.debug:
            return 1
        

        self.turnOff()
        time.sleep(4)
        self.arduinoReady.wait()
        self.arduinoReady.clear()        
        self.arduino.write(b"I") #turn the GoPro on
        try:
            while self.arduino.readline()!=b'ON\r\n':
                time.sleep(1)
            
            if self.osvServer:                             #tell the user the goPro just turned on (used for the old way)
                if self.takePhotoNow.isSet():
                    self.osvServer.canMove()
            else:
                print("Camera on")
            time.sleep(3)
            self.arduinoReady.set()
            self.changeMode()
            time.sleep(2)
            if self.__takePhoto(force=True):
                print(color.OKBLUE+"GoPro on",color.ENDC)
                return 1
            else:
                print(color.FAIL+"GoPro failed to turn on",color.ENDC)
                return 0
                
        except serial.SerialException as e:
            print(e)
            self.arduinoReady.set()
            return 0
            
            
    def pingChecking(self):
        """
        check that all camera are connected by pinging them
        """
        
        fail_list = self.ping(EYEFI_IP)
        if fail_list:
            print(color.WARNING+"SOME CARD DIDN'T ANSWER, NEW PING SESSION",color.ENDC)
            error = self.ping(fail_list)
        else:
            error = None
        
        if error:
            print(color.FAIL+"ALL THOSE IP FAILED TO PING TWICE:",color.ENDC)
            for ip in error:
                print(color.FAIL+str(ip),color.ENDC)
            return 0
        else:
            return 1

        print(color.ENDC,end="")
            
        
    def turnOff(self):
        """
        turn all GoPro off
        """
        if self.debug:
            return 1
        self.arduinoReady.wait()
        self.arduinoReady.clear()
        
        try:
            self.arduino.write(b"I") #turn the GoPro on
            while self.arduino.readline()!=b'ON\r\n':
                time.sleep(1)
            self.arduino.write(b"O") #turn the GoPro off        
            while self.arduino.readline()!=b"OFF\r\n":
                time.sleep(1)
            self.arduinoReady.set()
            print(color.OKBLUE+"GoPro off",color.ENDC)
            return 1
            
        except serial.SerialException as e:
            print(color.FAIL+str(e),color.ENDC)
            self.arduinoReady.set()
            return 0

    
    def changeMode(self):
        """
        change all GoPro mode
        """
        if self.debug:
            return 1
        self.arduinoReady.wait()
        self.arduinoReady.clear()
        self.arduino.write(b"M") #turn the GoPro on
        try:
            while self.arduino.readline()!=b'PHOTO_MODE\r\n':
                time.sleep(1)
            print(color.OKBLUE+"GoPro mode changed",color.ENDC)
        
        except serial.SerialException as e:
            print(e)
        self.arduinoReady.set()                
        
    def stop(self):
        """
        stop the thread
        """
        print(color.OKBLUE+"Stopping GoPro Thread...",color.ENDC)
        self.keepAlive.clear()
        print(color.OKGREEN+"GoPro Thread stopped",color.ENDC)
        
    def run(self):
        """
        a thread takin picture when needed
        """
        self.keepAlive.set()
        while self.keepAlive.isSet():
            self.takePhotoNow.wait()#wait for the server to ask for a picture
            if not self.debug:               
                self.arduinoReady.wait()        
                self.__takePhoto()                
            self.takePhotoNow.clear()
                        
    def __takePhoto(self,force = False):
        """
        private way to take photo (new way)
        """
        if self.debug:
            return 1

        if not force:
            assert self.arduinoReady.isSet()
            assert self.takePhotoNow.isSet()
        self.arduino.write(b"T") #turn the GoPro on
        try:
            answer = b''
            while answer not in (b'ERROR\r\n',b'TAKEN\r\n'):
                time.sleep(1)
                answer = self.arduino.readline()
            if answer == b'TAKEN\r\n':
                print(color.OKGREEN+"GoPro took photo",color.ENDC)
                if self.osvServer:
                    self.osvServer.statut(True) #tell the osvServer the picTaking succed
                else:
                    print("Pic taking succed")
                return 1
                    
            elif answer == b'ERROR\r\n':
                print(color.FAIL+"GoPro failed to take photo",color.ENDC)
                fail=self.arduino.readline().decode("ascii")
                for i in range(6):
                    if fail[i] == "1":
                        print("GoPro "+str(5-i)+" failed")

                if self.osvServer:
                    self.osvServer.statut(False,goProFailed=fail) #tell the osvServer the picTaking failed
                else:
                    print("Pic taking failed")                    
                return 0

        except serial.SerialException as e:
            print(e)
            
   
    def takePhoto(self):
        """
        ask all device to take a picture
        """        
        if self.takePhotoNow.isSet():
            return 0
        else:
            self.takePhotoNow.set()
            return 1       
        
        
    def ping(self,ipList):
        """
        ping all ip in the list and tell wich one doesn't answer
        """
        error = []

        for ip in ipList:            
            if not subprocess.call("ping -c 1 "+ip,shell=True):
                print(color.OKGREEN+str(ip),"CONNECTED : OK",color.ENDC)
            else:
                print(color.FAIL+str(ip),"NOT CONNECTED : ERROR",color.ENDC)
                error.append(ip)
        return error

if __name__=="__main__":
    print("Test des GoPro")
    goPro = GoPro()
    print("Allumage : ")
    if goPro.turnOn():
        print(color.OKGREEN+"Allumage OK")
    else:
        print(color.FAIL+"Allumage PAS OK")
        
#    goPro.changeMode()
#    time.sleep(1)

    while goPro.succed:
        goPro.takePhoto()
#        time.sleep(1)
    print("Extinction : ")
    if goPro.turnOff():
        print(color.OKGREEN+"Extinction OK")
    else:
        print(color.FAIL+"Extinction PAS OK")


