import os
import logging
from logging.handlers import RotatingFileHandler

from rederbro.utils.dataSend import DataSend

class Server():
    def __init__(self, config, serverType):
        self.config = config
        self.serverType = serverType

        #init pipe using dataSend class
        self.pipe = DataSend(os.path.dirname(os.path.abspath(__file__))+"/"+self.serverType+"/"+self.serverType+".pipe", "server")

        #init logger
        self.logFile = os.path.dirname(os.path.abspath(__file__))+"/../log/"+self.serverType+"_server.log"

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(self.serverType+' %(asctime)s :: %(levelname)s :: %(message)s')

        file_handler = RotatingFileHandler(self.logFile, 'a', 1000000, 1)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        self.delay = self.config["server"]["delay"]

        self.fakeMode = False
        self.running = True

    def setDebug(self, debug):
        """
        Allow you to change the logger level to debug or to info
        """
        if debug:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Debug mode set on")
        else:
            self.logger.setLevel(logging.INFO)
            self.logger.info("Debug mode set off")

    def setFakeMode(self, fakeMode):
        """
        Change fake mode
        """
        self.fakeMode = fakeMode
        self.logger.info("Fake mode set to {}".format(self.fakeMode))

    def start():
        """
        Method called by server command
        Must be overwrited
        """
        pass