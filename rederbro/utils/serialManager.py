import serial


class SerialManager():
    """
    This class allow you to send msg to an serial and wait her answer
    """

    def __init__(self, config, logger, serialName):
        self.config = config
        self.logger = logger

        try:
            self.serial = serial.Serial(config[serialName]["serial"], timeout=0.5, baudrate=config[serialName]["baudrate"])
        except Exception:
            self.serial = serial.Serial(config[serialName]["serial"], timeout=0.5)

        self.time_out = config[serialName]["time_out"]

    def sendMsg(self, msg, correctAnswer):
        """
        Send msg to the serial
        This method with send the msg and wait the answer.
        It will return if the answer send by serial is not correctAnswer and return the bad anwswer or None
        """

        # send msg to serial
        # msg must be convert in byte
        self.serial.write(msg.encode())
        self.logger.debug("{} send to serial".format(msg.encode()))

        # Wait for the answer of serial  if the answer of serial is not correctAnswer error will be True
        # BadAnswer will be answer send by serial
        error, badAnswer = self.waitAnswer(correctAnswer)

        return (error, badAnswer)

    def waitAnswer(self, correctAnswer, timeout=None):
        """
        Wait the answer of the serial with an time out
        Check if it is correct or not and return it
        """
        if timeout is None:
            checkNB = int(self.time_out / 0.5)
        else:
            checkNB = int(timeout / 0.5)
        # we will check checkNB time the answer before time out

        msg = ""

        for i in range(checkNB):
            answer = self.serial.readline()
            self.logger.debug("{} receive from serial".format(answer))
            msg += answer.decode()

            if "\r\n" in msg:
                break

        error = True

        if msg == correctAnswer+"\r\n":
            error = False

        return (error, msg)

    def clear(self):
        self.logger.info("Start clear serial")
        error, answer = self.waitAnswer("", timeout=2)
        self.logger.debug("{} was in serial".format(answer))
        self.logger.info("Serial cleared")
