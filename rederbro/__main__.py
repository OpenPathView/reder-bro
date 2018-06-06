#!/usr/bin/env python

from docopt import docopt
from rederbro.utils.config import Config
from rederbro.command.command import Command
from rederbro.command.serverCommand import ServerCommand

__doc__ = """Open path view rederbro

Usage:
  opv server main on
  opv server gopro on
  opv server sensors on
  opv server campaign on
  opv gopro relay STATUS
  opv gopro takepic
  opv gopro clear
  opv gopro STATUS
  opv gopro debug STATUS
  opv gopro fake STATUS
  opv sensors debug STATUS
  opv sensors fake STATUS
  opv sensors automode STATUS
  opv sensors distance METER
  opv sensors cord
  opv campaign new NAME
  opv campaign attach NAME

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
        Command(config, args[0]).run(args[1])
    else:
        ServerCommand(config, args[0]).run(args[1])


if __name__ == "__main__":
    main()
