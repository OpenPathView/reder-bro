from docopt import docopt
from rederbro.utils.config import Config
from rederbro.command.command import Command
from rederbro.command.serverCommand import ServerCommand
from rederbro.command.goproCommand import GoproCommand
from rederbro.command.sensorsCommand import SensorsCommand

__doc__ ="""Open path view rederbro

Usage:
  opv server main on
  opv server gopro on
  opv server sensors on
  opv gopro relay on
  opv gopro relay off
  opv gopro on
  opv gopro off
  opv gopro takepic
  opv gopro debug on
  opv gopro debug off
  opv gopro fake off
  opv gopro fake on
  opv gopro clear
  opv sensors debug on
  opv sensors debug off
  opv sensors fake on
  opv sensors fake off

Options:
  -h --help     Show this screen.

"""

command_list = {"server" : ServerCommand, "gopro": GoproCommand, "sensors" :  SensorsCommand}

config = Config().getConf()

def main():
    #get argmuent parsed by docopt
    args = docopt(__doc__)
    #reparse and check argument given by docopt
    parsedArgs = Config().checkargs(args)
    # parsedArgs --> (a (b, c))
    # a --> command name see command_list dict
    # b --> subcommand name see command __doc__ variable
    # c --> True or False like On or Off in __doc__ variable

    launchCommand(parsedArgs)

def launchCommand(args):
    #launch command by using a dict and give args[1] to the command
    # args[0] --> command name
    # args[1] --> (a, b)
    # a --> sub command name
    # b --> sub command argument
    command_list[args[0]](config).run(args[1])


if __name__ == "__main__":
    main()
