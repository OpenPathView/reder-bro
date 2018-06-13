import zmq
import socket


class Command():
    def __init__(self, config, topic, answer=False):
        self.config = config
        self.topic = topic
        self.server_url = config["server"]["server_url"]
        self.server_port = config["server"]["client_server_port"]
        self.url = "tcp://{}"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.answer = self.context.socket(zmq.PULL)
        self.askAnswer = answer

    def sendMsg(self, args):
        """
        Used to send a msg to main server using url and port found in config
        msg must be a string who contain a json to be undertand by the server
        """

        self.socket.connect((self.url+":{}").format(self.server_url, self.server_port))
        if self.askAnswer:
            args["answer_port"] = self.answer.bind_to_random_port(self.url.format(self.config["server"]["bind_address"]))
            args["answer_url"] = socket.gethostbyname(socket.gethostname())
        self.socket.send_json(args)
        if self.askAnswer:
            data = self.answer.recv_json()
            print("{}\nError : {}".format(data["msg"], data["error"]))

    def run(self, args):
        """
        Method called by main class
        Must be overwrited
        """
        msg = {}
        msg["command"] = args[0]
        msg["args"] = args[1]
        msg["topic"] = self.topic

        self.sendMsg(msg)
