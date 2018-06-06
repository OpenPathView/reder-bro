# Rederbro
Rederbro is the application put on the Open path view backpack (rederbro).
This application manage camera, sensors and data storage of rederbro backpack.

## Requirement
To use this application you must install all python3 requirement (you should do this in a virtual env):
```bash
pip install -r requirement.txt
```
It will mainly download zmq which is a network library

## Network
Rederbro work with server which are all independant, actually there are four server :

  * Main server which is just a router between all server
  * Gopro server which manage all camera, it use to turn on camera, take picture...
  * Sensors server which manage all sensors
  * Campaign server which store all taken picture, gps position, and time. All these information are stored with a csv file. This server is needed to use [opv-import](https://github.com/OpenPathView/OPV_importData)

As I said before all server are independant but there are some exception :

  * All server need main server to work
  * Campaign server need sensors server to work

## How to use ?
Before using rederbro you must install rederbro application :
```bash
python setup.py install
#You can use develop instead of install to make change in the application
#Of course it's a python3 application =)
```

I don't advise to install it with ```pip -e``` cause you will don't have access to log and campaign csv

Next to had documentation about available command you can use :
```bash
rederbro --help
```

To fully use rederbro you should start all server. The easiest way to do that is to make systemd service.
Next you can use a tmux to see log.

## Android application
You can control the application by using shell command, but the simplest way is to use the android application (not publish yet) to manage rederbro.
