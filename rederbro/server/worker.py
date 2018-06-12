import os
import logging
import zmq
from logging.handlers import RotatingFileHandler


class Worker():
    def __init__(self, config, name):
        self.config = config
        self.name = name

        # init logger
        self.logFile = os.path.dirname(os.path.abspath(__file__))+"/../log/"+self.name+"_server.log"

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(self.name+' --- %(asctime)s :: %(levelname)s :: %(message)s')

        file_handler = RotatingFileHandler(self.logFile, 'a', 1000000, 1)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        self.logger.info("-----------------------------------------------")
        self.logger.info("Connecting to main server")
        url = "tcp://{}:{}".format(self.config["server"]["server_url"], self.config["server"]["worker_server_port"])
        urlGPS = "tcp://{}:{}".format(self.config["gps"]["server_url"], self.config["gps"]["pub_server_port"])

        self.context = zmq.Context()
        self.poller = zmq.Poller()

        self.gps_info = self.context.socket(zmq.SUB)
        self.gps_info.connect(urlGPS)
        self.gps_info.setsockopt_string(zmq.SUBSCRIBE, "")

        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(url)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.poller.register(self.socket, zmq.POLLIN)

        self.answer = self.context.socket(zmq.PUSH)

        self.fakeMode = False
        self.running = True

    def setDebug(self, debug):
        """
        Allow you to change the logger level to debug or to info
        """
        if debug == "on":
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Debug mode set on")
        else:
            self.logger.setLevel(logging.INFO)
            self.logger.info("Debug mode set off")

        return {
            "debug": debug
        }

    def setFakeMode(self, fakeMode):
        """
        Change fake mode
        """
        self.fakeMode = True if fakeMode == "on" else False
        self.logger.info("Fake mode set to {}".format(self.fakeMode))

        return {
            "fakemode": self.fakeMode
        }

    def start(self):
        """
        Method called by server command
        """
        self.logger.warning("Server started")
        while self.running:
            self.checkCommand()

    def pollCall(self, poll):
        pass

    def checkCommand(self):
        # check data send by main server
        poll = dict(self.poller.poll())

        if self.socket in poll:
            cmd = self.socket.recv_json()
            self.logger.debug(cmd)

            if cmd["topic"] == self.name:
                try:
                    if self.command[cmd["command"]][1]:
                        rep = self.command[cmd["command"]][0](cmd["args"])
                    else:
                        rep = self.command[cmd["command"]][0]()

                    if "answer_port" in cmd and "answer_url" in cmd:
                        url = "tcp://{}:{}".format(cmd["answer_url"], cmd["answer_port"])
                        self.answer.connect(url)
                        self.answer.send_json(rep)
                        self.answer.disconnect(url)


                except Exception as e:
                    self.logger.exception(e)

        self.pollCall(poll)
