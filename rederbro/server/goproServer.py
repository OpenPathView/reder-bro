from rederbro.server.worker import Worker
from rederbro.utils.serialManager import SerialManager
from rederbro.command.command import Command
import time

try:
    import RPi.GPIO as GPIO
except Exception:
    pass


class GoproServer(Worker):
    """
    """
    def clear(self):
        """
        Simply clear serial to arduino,
        it can be useful if the arduino start after rederbro.
        """
        if self.fakeMode:
            self.logger.info("Arduino serial cleared")
        else:
            self.arduino.clear()

        return {
            "msg": "Serial cleared",
            "error": False
        }

    def turnGoproOn(self, full=True):
        """
        Turn all gopro on,
        It ask arduino to do it
        Turn full to True allow to put gopro in photo mode
        """
        error, answer = self.arduino.sendMsg("I", "ON")

        if error:
            self.logger.error("Failed to turn gopro on")
            self.goproOn = False

        else:
            if full:
                time.sleep(0.5)
                error = self.changeMode(force=True)

                if error:
                    self.logger.error("Failed to turn gopro on")
                    self.goproOn = False

                else:
                    self.logger.info("Gopro turned on (full mode)")
                    self.goproOn = True

            else:
                self.logger.info("Gopro turned on (not full mode)")
                self.goproOn = True

        return {
            "msg": "Gopro turned {}".format("on" if self.goproOn else "off"),
            "error": error
        }

    def turnGoproOff(self):
        """
        Turn all gopro off,
        It ask arduino to do it
        """
        if not self.goproOn:
            self.turnGoproOn(full=False)

        error, answer = self.arduino.sendMsg("O", "OFF")

        if error:
            self.logger.error("Failed to turn gopro off")
            self.goproOn = True

        else:
            self.logger.info("Gopro turned off")
            self.goproOn = False

        return {
            "msg": "Gopro turned {}".format("on" if self.goproOn else "off"),
            "error": error
        }

    def turnGopro(self, state):
        """
        Switch gopro to state value,
        It manage if server is in fakemode or if relay is OFF
        """
        self.logger.info("Turn gopro {}".format(state))
        answer = {}

        if self.relayOn:
            # relay must be on before switch on gopro
            if self.fakeMode:
                # when fake mode is on
                self.goproOn = state
                self.logger.info("Turned gopro {} (fake mode)".format(state))

                return {
                    "msg": "Gopro turned {}".format("on" if self.goproOn else "off"),
                    "error": self.goproOn
                }

            else:
                if state == "on":
                    answer = self.turnGoproOn()
                else:
                    answer = self.turnGoproOff()

        else:
            self.logger.error("Failed to change gopro status cause relay is off")
            self.goproOn = False
            return {
                "msg": "Gopro turned {} cause relay is off".format("on" if self.goproOn else "off"),
                "error": True
            }

        return answer

    def turnRelay(self, state):
        """
        Switch relay to state value
        """
        self.logger.info("Turn relay {}".format(state))

        if self.fakeMode:
            # when fake mode is on
            self.relayOn = state
            self.logger.info("Turned relay {} (fake mode)".format(state))

        else:
            # when fake mode is off
            if state == "on":
                GPIO.output(self.config["relay_pin"], GPIO.HIGH)
                self.relayOn = True
            else:
                GPIO.output(self.config["relay_pin"], GPIO.LOW)
                self.relayOn = False
                self.goproOn = False

            self.logger.info("Turned relay {}".format(state))

        return {
            "msg": "Relay turned {} and gopro is {}".format("on" if self.relayOn else "off", "on" if self.goproOn else "off"),
            "error": False
        }

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
                error, answer = self.arduino.sendMsg("M", "PHOTO_MODE")

                if error:
                    self.logger.error("Failed to change gopro mode")
                    return True
                else:
                    self.logger.info("Gopro mode is photo")
                    return False
            else:
                self.logger.error("Failed to change gopro mode cause gopro is off")
                return True

    def askCampaign(self, goproFail):
        args = {}
        args["time"] = time.asctime()
        args["goproFail"] = goproFail
        msg = ("add_picture", args)
        cmd = Command(self.config, "campaign")
        cmd.run(msg)

    def takePic(self, force=False):
        """
        Ask arduino to take picture
        """
        self.logger.info("Take picture")

        if force or self.goproOn:
            if self.fakeMode:
                self.logger.info("Gopro took picture (fake mode)")
                self.askCampaign("000000")
                answer = {
                    "msg": "All gopro took picture",
                    "error": False
                }

            else:
                errorNB = 0

                error, answer = self.arduino.sendMsg("T", "ID2")
                errorNB += 1 if error else 0

                error, answer = self.arduino.waitAnswer("ID1s")
                errorNB += 1 if error else 0

                goproFail = [[], "000000"]
                if error:
                    error, answer = self.arduino.waitAnswer("")
                    goproFail[1] = answer
                    for i in range(len(answer)):
                        if answer[i] == "1":
                            goproFail[0].append(5-i)

                    error, answer = self.arduino.waitAnswer("ID1s")
                    self.logger.error("Gopro {} failed to take picture".format(goproFail[0]))

                error, answer = self.arduino.waitAnswer("TAKEN")
                errorNB += 1 if error else 0

                if errorNB == 0:
                    self.logger.info("All gopro took picture")
                else:
                    self.logger.info("Gopro failed to took picture")

                self.askCampaign(goproFail[1])

                answer = {
                    "msg": "Gopro took picture except gopro : {}".format(", ".join(goProFailed[0])) if errorNB > 0 else "All gopro took picture",
                    "error": False if errorNB == 0 else True
                }

        else:
            self.logger.error("Gopro can't take picture cause gopro is off")
            answer = {
                "msg": "Gopro is off so I can't take picture",
                "error": True
            }

        return answer

    def __init__(self, config):
        # Use the __init__ of the server class
        Worker.__init__(self, config, "gopro")

        self.goproOn = False
        self.relayOn = False

        try:
            # init arduino
            self.arduino = SerialManager(self.config, self.logger, "arduino")
            self.clear()
        except Exception as e:
            self.logger.error("Can't connect to arduino ({})".format(e))
            self.setFakeMode("on")

        try:
            # init GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.config["relay_pin"], GPIO.OUT)
        except Exception as e:
            self.logger.error("Not on a rpi ({})".format(e))
            if not self.fakeMode:
                self.setFakeMode("on")

        # switch off relay to be sure that gopro are off
        self.turnRelay(False)

        # dict who link a command to a method
        # a : (b, c)
        # a --> command name
        # b --> method who can treat the command
        # c --> if there are argument for the method
        self.command = {
            "debug": (self.setDebug, True),
            "fake": (self.setFakeMode, True),
            "gopro": (self.turnGopro, True),
            "relay": (self.turnRelay, True),
            "takepic": (self.takePic, False),
            "clear": (self.clear, False)
        }
