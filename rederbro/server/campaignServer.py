from rederbro.server.worker import Worker
import os
import zmq
import csv


class CampaignServer(Worker):
    def add_picture(self, picInfo):
        self.logger.debug("Ask sensors data")
        self.pictureNB += 1
        self.gps_infoReq.send_json({})
        try:
            self.logger.debug("Receive sensors data")
            self.sensorsJson = self.gps_infoReq.recv_json()
        except Exception as e:
            self.setSocketReq()
            self.logger.debug(e)

        text = "{}; {}; {}; {}; {}; {}; {}; {}; {}\n".format(
            self.pictureNB,
            picInfo["time"],
            self.sensorsJson["lat"],
            self.sensorsJson["lon"],
            self.sensorsJson["alt"],
            self.sensorsJson["head"],
            self.sensorsJson["time"],
            self.sensorsJson["battVoltage"],
            picInfo["goproFail"]
        )

        self.logger.info("{} will be put in csv file".format(text))

        with open(self.currentCampaignPath, "a") as csv:
            csv.write(text)

        self.campaign_infoPub.send_json({
            "info": "Picture taken",
            "error": picInfo["goproFail"],
            "self.sensorsJson": self.sensorsJson
            })

        return {
            "msg": "A new picture register to {} csv, the line is {}".format(self.currentCampaign,  text),
            "error": False
        }

    def newCampaign(self, args):
        self.attachCampaign(args)

        with open(self.currentCampaignPath, "w") as csv:
            csv.write("number; time; lat; lon; alt; rad; self.sensorsJson_time; voltage; goProFailed\n")

        self.logger.info(args+" campaign created")
        return {
            "msg": "Campaign {} succefuly created and attached".format(self.currentCampaign),
            "error": False
        }

    def attachCampaign(self, args):
        self.currentCampaignPath = self.baseCampaignPath + args + ".csv"
        self.currentCampaign = args
        self.logger.info("Campaign attached to "+args)

        return {
            "msg": "Campaign {} succefuly attached".format(self.currentCampaign),
            "error": False
        }

    def pollCall(self, poll):
        if self.campaign_infoRep in poll:
            self.campaign_infoRep.recv_json()
            self.logger.info("Someone ask the campaign info")
            rep = []

            with open(self.currentCampaignPath) as file:
                csvFile = csv.reader(file, skipinitialspace=True, delimiter=';')
                csvFile = [row for row in csvFile]

            fields = csvFile[0]
            del csvFile[0]
            for line in csvFile:
                lineJson = {}
                for i in range(len(fields)):
                    lineJson[fields[i]] = line[i]
                rep.append(lineJson)

            self.logger.debug("Answer sent : {}".format(rep))
            self.campaign_infoRep.send_json(rep)

    def __init__(self, config):
        # Use the __init__ of the server class
        Worker.__init__(self, config, "campaign")

        self.baseCampaignPath = os.path.dirname(os.path.abspath(__file__))+"/../campaign/"

        self.currentCampaign = "picturesInfo"
        self.newCampaign(self.currentCampaign)

        self.pictureNB = 0

        # dict who link a command to a method
        # a : (b, c)
        # a --> command name
        # b --> method who can treat the command
        # c --> if there are argument for the method
        self.command = {
            "add_picture": (self.add_picture, True),
            "new": (self.newCampaign, True),
            "attach": (self.attachCampaign, True),
            "debug": (self.setDebug, True)
        }

        self.url_gps = "tcp://{}:{}".format(self.config["gps"]["server_url"], self.config["gps"]["rep_server_port"])

        self.campaign_infoPub = self.context.socket(zmq.PUB)
        self.campaign_infoPub.bind("tcp://{}:{}".format(self.config["campaign"]["bind_url"], self.config["campaign"]["pub_server_port"]))

        self.campaign_infoRep = self.context.socket(zmq.REP)
        self.campaign_infoRep.bind("tcp://{}:{}".format(self.config["campaign"]["bind_url"], self.config["campaign"]["rep_server_port"]))

        self.poller.register(self.campaign_infoRep, zmq.POLLIN)

        self.gps_infoReq = self.context.socket(zmq.REQ)
        # self.gps_infoReq.setsockopt(zmq.RCVTIMEO, (self.config["gps"]["time_out"] + 2)*1000)
        self.gps_infoReq.setsockopt(zmq.RCVTIMEO, 1000)
        self.gps_infoReq.setsockopt(zmq.REQ_RELAXED, 1)
        self.gps_infoReq.setsockopt(zmq.REQ_CORRELATE, 1)
        self.gps_infoReq.connect(self.url_gps)

        self.setSocketReq(close=False)

        self.sensorsJson = {
            "lat": 0,
            "lon": 0,
            "alt": 0,
            "head": 0,
            "battVoltage": 0,
            "time": 0
        }

    def setSocketReq(self, close=True):
        if close:
            self.gps_infoReq.close()
        self.gps_infoReq = self.context.socket(zmq.REQ)
        self.gps_infoReq.setsockopt(zmq.RCVTIMEO, (self.config["gps"]["time_out"] + 2)*1000)
        self.gps_infoReq.connect(self.url_gps)
