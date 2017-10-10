from rederbro.server.server import Server
from rederbro.utils.arduino import Arduino
import time

try:
    from RPi.GPIO import GPIO
except:
    pass

class GoproServer(Server):
    def clear(self):
        if self.fakeMode:
            self.logger.info("Arduino serial cleared")
        else:
            self.arduino.clear()

    def turnGopro(self, state, full=True):
        """
        Switch gopro to state value
        """
        self.logger.info("Turn gopro {}".format(state))

        if self.relayOn:
            #relay must be on before switch on gopro
            if self.fakeMode:
                #when fake mode is on
                self.goproOn = state
                self.logger.info("Turned gopro {} (fake mode)".format(state))

            else:
                #when fake mode is off
                if state:
                    #turn on
                    error, answer = self.arduino.sendMsg("I", "ON\r\n")

                    if error:
                        self.logger.error("Failed to turn gopro on")
                        self.goproOn = False
                        return self.goproOn

                    else:
                        if full:
                            error = self.changeMode(force=True)

                            if error:
                                self.logger.error("Failed to turn gopro on")
                                self.goproOn = False
                                return self.goproOn

                            else:
                                self.logger.info("Gopro turned on (full mode)")
                                self.goproOn = True
                                return self.goproOn

                        else:
                            self.logger.info("Gopro turned on (not full mode)")
                            self.goproOn = True
                            return self.goproOn

                else:
                    #turn off
                    if not self.goproOn:
                        self.turnGopro(True, full=False)

                    error, answer = self.arduino.sendMsg("O", "OFF\r\n")

                    if error:
                        self.logger.error("Failed to turn gopro off")
                        self.goproOn = True
                        return self.goproOn

                    else:
                        self.logger.info("Gopro turned off")
                        self.goproOn = False
                        return self.goproOn
        else:
            self.logger.error("Failed to change gopro status cause relay is off")
            self.goproOn = False
            return self.goproOn


    def turnRelay(self, state):
        """
        Switch relay to state value
        """
        self.logger.info("Turn relay {}".format(state))

        if self.fakeMode:
            #when fake mode is on
            self.relayOn = state
            self.logger.info("Turned relay {} (fake mode)".format(state))

        else:
            #when fake mode is off
            if state:
                GPIO.output(self.config["relay_pin"], GPIO.HIGH)
                self.relayOn = True
            else:
                GPIO.output(self.config["relay_pin"], GPIO.LOW)
                self.relayOn = False
                self.goproOn = False

            self.logger.info("Turned relay {}".format(state))

    def changeMode(self, force=False):
        """
        Ask arduino to set gopro mode to photo
        """
        self.logger.info("Change gopro mode to photo")

        if self.fakeMode:
            self.logger.info("Gopro mode is photo")
            return False
        else:
            if force or self.goproOn:
                error, answer = self.arduino.sendMsg("M", "PHOTO_MODE\r\n")

                if error:
                    self.logger.error("Failed to change gopro mode")
                    return True
                else:
                    self.logger.info("Gopro mode is photo")
                    return False
            else:
                self.logger.error("Failed to change gopro mode cause gopro is off")
                return True

    def takePic(self, force=False):
        """
        Ask arduino to take picture
        """
        self.logger.info("Take picture")
        if self.fakeMode:
            self.logger.info("Gopro took picture")
            return False

        if force or self.goproOn:
            errorNB = 0

            error, answer = self.arduino.sendMsg("T", "ID2\r\n")
            errorNB += 1 if error else 0

            error, answer =  self.arduino.waitAnswer("ID1s\r\n")
            errorNB += 1 if error else 0

            goproFail = []
            if error:
                error, answer =  self.arduino.waitAnswer("")
                for i in range(len(answer)):
                    if answer[i] == "1":
                        goproFail.append(i)

                error, answer =  self.arduino.waitAnswer("ID1s\r\n")
                self.logger.error("Gopro {} failed to take picture".format(goproFail))

            error, answer =  self.arduino.waitAnswer("TAKEN\r\n")
            errorNB += 1 if error else 0

            if errorNB == 0:
                self.logger.info("All gopro took picture")
                return False
            else:
                self.logger.info("Gopro failed to took picture")
                return True
        else:
            self.logger.error("Gopro can't take picture cause gopro is off")
            return True

    def __init__(self, config):
        #Use the __init__ of the server class
        Server.__init__(self, config, "gopro")


        try:
            #init arduino
            self.arduino = Arduino(self.config, self.logger)
            self.clear()
        except:
            self.logger.error("Can't connect to arduino")
            self.setFakeMode(True)

        try:
            #init GPIO
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            GPIO.setup(self.config["relay_pin"], GPIO.OUT)
        except:
            self.logger.error("Not on a rpi")
            if not self.fakeMode:
                self.setFakeMode(True)

        #switch off relay to be sure that gopro are off
        self.turnRelay(False)

        self.goproOn = False
        self.relayOn = False

        #dict who link a command to a method
        # a : (b, c)
        # a --> command name
        # b --> method who can treat the command
        # c --> argument for the method
        self.command = {\
        "debugOn" : (self.setDebug, True),\
        "debugOff" : (self.setDebug, False),\
        "fakeOn" : (self.setFakeMode, True),\
        "fakeOff" : (self.setFakeMode, False),\
        "goproOn" : (self.turnGopro, True),\
        "goproOff" : (self.turnGopro, False),\
        "relayOn" : (self.turnRelay, True),\
        "relayOff" : (self.turnRelay, False),\
        "takepicOn" : (self.takePic, None),\
        "clearOn" : (self.clear, None)\
        }

    def start(self):
        self.logger.warning("Server started")
        while self.running:
            #check data send by main server
            text = self.pipe.readText()

            for line in text:
                #if method who treat the command take an argument
                if self.command[line][1] is not None:
                    #treat command
                    self.command[line][0](self.command[line][1])
                else:
                    #treat command
                    self.command[line][0]()

            #if command receive by main server is not empty clear the pipe
            if len(text) is not 0:
                self.pipe.clean()

            time.sleep(self.delay)
