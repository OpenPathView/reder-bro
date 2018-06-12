#!/usr/bin/env python

from docopt import docopt
from rederbro.utils.config import Config
from rederbro.command.command import Command
from rederbro.command.serverCommand import ServerCommand

__doc__ = """Open path view rederbro

Usage:
  rederbro server main on
  rederbro server gopro on
  rederbro server sensors on
  rederbro server campaign on
  rederbro gopro relay STATUS
  rederbro gopro takepic
  rederbro gopro clear
  rederbro gopro STATUS
  rederbro gopro debug STATUS
  rederbro gopro fake STATUS
  rederbro sensors debug STATUS
  rederbro sensors fake STATUS
  rederbro sensors automode STATUS
  rederbro sensors distance METER
  rederbro sensors get
  rederbro campaign new NAME
  rederbro campaign attach NAME
  rederbro campaign debug STATUS

Options:
  -h --help     Show this screen.

"""

config = Config().getConf()


def main():
    # get argmuent parsed by docopt
    args = docopt(__doc__)
    # reparse and check argument given by docopt
    parsedArgs = Config().checkargs(args)
    # parsedArgs --> (a (b, c))
    # a --> command name see command_list dict
    # b --> subcommand name see command __doc__ variable
    # c --> True or False like On or Off in __doc__ variable

    launchCommand(parsedArgs)


def launchCommand(args):
    # launch command by using a dict and give args[1] to the command
    # args[0] --> command name
    # args[1] --> (a, b)
    # a --> sub command name
    # b --> sub command argument
    if args[0] != "server":
        Command(config, args[0], answer=True).run(args[1])
    else:
        ServerCommand(config, args[0]).run(args[1])


if __name__ == "__main__":
    main()
