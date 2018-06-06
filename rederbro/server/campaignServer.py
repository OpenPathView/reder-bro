from rederbro.server.worker import Worker
import os
import zmq
import csv


class CampaignServer(Worker):
    def add_picture(self, picInfo):
        self.pictureNB += 1
        self.gps_infoReq.send_json({})
        gps = self.gps_infoReq.recv_json()
        text = "{}; {}; {}; {}; {}; {}; {}; {}\n".format(
            self.pictureNB,
            picInfo["time"],
            gps["lat"],
            gps["lon"],
            gps["alt"],
            gps["head"],
            gps["time"],
            picInfo["goproFail"]
        )

        self.logger.info("{} will be put in csv file".format(text))

        with open(self.currentCampaignPath, "a") as csv:
            csv.write(text)

        self.campaign_infoPub.send_json({"info": "Picture taken", "error": picInfo["goproFail"]})

    def newCampaign(self, args):
        self.attachCampaign(args)

        with open(self.currentCampaignPath, "w") as csv:
            csv.write("number; time; lat; lon; alt; rad; gps_time; goProFailed\n")

        self.logger.info(args+" campaign created")

    def attachCampaign(self, args):
        self.currentCampaignPath = self.baseCampaignPath + args + ".csv"
        self.logger.info("Campaign attached to "+args)

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

        self.newCampaign("pictureInfo")

        self.pictureNB = 0

        # dict who link a command to a method
        # a : (b, c)
        # a --> command name
        # b --> method who can treat the command
        # c --> if there are argument for the method
        self.command = {
            "add_picture": (self.add_picture, True),
            "new": (self.newCampaign, True),
            "attach": (self.attachCampaign, True)
        }

        urlGPS = "tcp://{}:{}".format(self.config["gps"]["server_url"], self.config["gps"]["rep_server_port"])

        self.campaign_infoPub = self.context.socket(zmq.PUB)
        self.campaign_infoPub.bind("tcp://{}:{}".format(self.config["campaign"]["bind_url"], self.config["campaign"]["pub_server_port"]))

        self.campaign_infoRep = self.context.socket(zmq.REP)
        self.campaign_infoRep.bind("tcp://{}:{}".format(self.config["campaign"]["bind_url"], self.config["campaign"]["rep_server_port"]))

        self.poller.register(self.campaign_infoRep, zmq.POLLIN)

        self.gps_infoReq = self.context.socket(zmq.REQ)
        self.gps_infoReq.connect(urlGPS)
