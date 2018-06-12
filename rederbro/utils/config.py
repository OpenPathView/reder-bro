import json
import os


class Config():
    def __init__(self):
        self.configFile = os.path.dirname(os.path.abspath(__file__))+"/../config.json"
        self.config = self.loadConf()

        # list of all command
        self.mainCommand = ["server", "sensors", "gopro", "campaign"]

        # commandArgs --> a dict who contain all sub command of a command and if it take an argument
        # a : ((b, (c, d)), ...)
        # a --> command name
        # b --> sub command name
        # c --> if sub command take an argument
        # d --> sub command argument
        # ...
        # if sub commmand take an argument it must be on-->True or off-->False
        self.commandArgs = {
            "gopro": (
                ("takepic", (False, None)),
                ("clear", (False, None)),
                ("relay", (True, "STATUS")),
                ("debug", (True, "STATUS")),
                ("fake", (True, "STATUS")),
                ("", (True, "STATUS"))),
            "sensors": (
                ("get", (False, None)),
                ("debug", (True, "STATUS")),
                ("fake", (True, "STATUS")),
                ("automode", (True, "STATUS")),
                ("distance", (True, "METER"))),
            "campaign": (
                ("new", (True, "NAME")),
                ("attach", (True, "NAME")),
                ("debug", (True, "STATUS"))),
            "server": (
                ("main", (True, "on")),
                ("sensors", (True, "on")),
                ("campaign", (True, "on")),
                ("gopro", (True, "on")))
        }

    def loadConf(self):
        """
        Load conf and convert it in dict
        """
        if self.configFile is not "":
            with open(self.configFile, 'r') as conf:
                config = json.load(conf)
        return config

    def checkargs(self, args):
        """
        Check if args given by docopt are usable and convert them in an usable tuple
        """

        # see self.commandArgs doc to understand
        for command in self.mainCommand:
            # check if this command is set in docopt argument
            if args[command]:
                for subcommand in self.commandArgs[command]:
                    # check if sub command is set in docopt argument
                    # args[0] can be empty when there are no sub commmand
                    if subcommand[0] == "" or args[subcommand[0]]:
                        # some sub command take no argument like takepic

                        if not subcommand[1][0]:
                            # return value --> (a (b, c))
                            # a --> command name
                            # b --> sub command name or command name when sub command name is empty
                            # c --> argument of sub command here True cause sub command take no argument
                            return (command, (subcommand[0] if subcommand[0] != "" else command, True))
                        else:
                            # return value --> (a (b, c))
                            # a --> command name
                            # b --> sub command name or command name when sub command name is empty
                            # c --> argument of sub command
                            return (command, (subcommand[0] if subcommand[0] != "" else command, args[subcommand[1][1]]))

    def getConf(self):
        return self.config
