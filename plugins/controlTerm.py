import time
import threading
import color
import curses
import os
import math
import tee

class ControlTerm(threading.Thread):
    """
    a control terminal to display information and let the user type in command
    """

    def __init__(self,opvServer=None):
        """
        init the term
        """
        print(color.OKBLUE+"ControlTerm : Initializing server...",color.ENDC)
        threading.Thread.__init__(self)
        self.daemon = True
        self.opvServer = opvServer

        self.lat = 0
        self.lon = 0
        self.alt = -42
        self.rad = 0

        self.battery_volatge = 0

        #init all the curses stuff
        self.stdscr = curses.initscr()  #the terminal window
        curses.noecho()                 #don't show the pressed key
        curses.cbreak()                 #don't wait for enter to get pressed key
        curses.nonl()                   #allow to get the enter key press
        self.stdscr.keypad(1)           #something... see internet, I forgot what it is for, but it's usefull, I think
        self.stdscr.clear()             #clear the screen
        curses.curs_set(0)              #hide cursor

        curses.start_color()            #enable colors and init them so we can convert ansi color to curses colors
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
        self.cursesColors = {color.HEADER[-3:]:curses.color_pair(4),
        color.OKBLUE[-3:]:curses.color_pair(2),
        color.OKGREEN[-3:]:curses.color_pair(3),
        color.WARNING[-3:]:curses.color_pair(1),
        color.FAIL[-3:]:curses.color_pair(5),
        color.ENDC[-3:]:curses.color_pair(0)}
        self.lastUsedColor = curses.color_pair(0)

        self.dispBuffer = ""            #buffer for data to be written

        nlines, ncols = self.stdscr.getmaxyx()              #stdscr take all the term size, but won't resize as he resize
        self.dispArea =  curses.newwin(nlines-2, ncols)   #the disp area is only the top area of the term
        self.dispArea.scrollok(True)

        self.logger = tee.Tee("opv.log","a",screenOut=self)


        self.commandArea = curses.newwin(1, ncols,nlines-1,0)
        self.commandArea.nodelay(1) #getch will be non blocking
        self.commandArea.keypad(1)
        self.keepAlive = threading.Event()

        self.start()
        print(color.OKGREEN+"ControlTerm : server initialized",color.ENDC)

    def write(self,txtToWrite):
        """
        write text in the buffer
        """
        self.dispBuffer += txtToWrite
        self.flush()

    def flush(self):
        """
        flush the buffered data to the screen
        """
        tmp = self.dispBuffer.split("\033[")
        for i  in tmp:
            if i[:3] in self.cursesColors.keys():
                self.lastUsedColor = self.cursesColors[i[:3]]
                i=i[3:]
            self.dispArea.addstr(i,self.lastUsedColor)
            self.dispArea.refresh()
        self.dispBuffer = ""

    def __del__(self):
        """
        uninitialise curses stuff
        """
        self.logger.__del__()
        curses.nocbreak()
        self.stdscr.keypad(0)
        self.commandArea.keypad(0)
        curses.echo()
        curses.nl()
        curses.endwin()
        print(color.WARNING+"ControlTerm : destroying",color.ENDC)

    def stop(self):
        """
        stop the thread
        """
        print(color.OKBLUE+"ControlTerm : Stopping thread...",color.ENDC)
        self.keepAlive.clear()
        print(color.OKGREEN+"ControlTerm :  Thread stopped",color.ENDC)

    def run(self):
        """
        main loop, get keyboard event and communicate with the opvServer
        """
        self.keepAlive.set()
        history = [""]       # history while be 50 element long
        cmdBackUp = ""
        cursorPos = 0
        index = len(history)-1    #last history element is the actual command
        t = self.commandArea.getch(0, cursorPos)
        self.commandArea.addch(0,cursorPos,t)
        self.commandArea.refresh()
        while self.keepAlive.isSet():
            key = self.commandArea.getch()
            if key==-1:
                time.sleep(0.001)
                continue
            elif key==curses.KEY_UP:
                if index==len(history)-1:
                    cmdBackUp = history[-1]
                index-=1
                if index <0:
                    index = 0
                history[-1] = history[index]
            elif key==curses.KEY_DOWN:
                index+=1
                if index >=len(history):
                    index = len(history)-1
                history[-1] = history[index]
                if index==len(history)-1:
                    history[-1]=cmdBackUp
            elif key==curses.KEY_LEFT:
                cursorPos-=1
                if cursorPos<0:
                    cursorPos = 0
                else:
                    y,x = self.commandArea.getyx()
                    self.commandArea.move(y,cursorPos)
            elif key==curses.KEY_RIGHT:
                cursorPos+=1
                if cursorPos>len(history[-1]):
                    cursorPos = len(history[-1])
                else:
                    y,x = self.commandArea.getyx()
                    self.commandArea.move(y,cursorPos)
            elif key==curses.KEY_BACKSPACE:
                history[-1]=history[-1][:cursorPos-1]+history[-1][cursorPos:]
                cursorPos-=1
                if cursorPos>len(history[-1]):
                    cursorPos = len(history[-1])
                if cursorPos<0:
                    cursorPos = 0
            elif key==curses.KEY_DC:
                history[-1]=history[-1][:cursorPos]+history[-1][cursorPos+1:]
                if cursorPos>len(history[-1]):
                    cursorPos = len(history[-1])
                if cursorPos<0:
                    cursorPos = 0
            elif key == 13: # curses.KEY_ENTER doesn't work, but 13 does...
                self.commandHandler(history[-1])
                history.append("")
                if len(history)>50:
                    history.pop(0)
                index = len(history)-1
                cursorPos = 0
            else:
                history[-1] = history[-1][:cursorPos]+chr(key)+history[-1][cursorPos:]
                cursorPos +=1
            self.commandArea.clear()
            try:
                self.commandArea.addstr(history[-1])
            except Exception as e:
                print(color.WARNING,e,"with string : ",history[-1],color.END)
            self.commandArea.chgat(0,cursorPos,1,curses.A_REVERSE)
            self.commandArea.refresh()

    def commandHandler(self,command):
        """
        handle given command
        """
        command = command.lower().split(" ")
        if len(command)==0:
            print("ControlTerm : No message")
        else:
            cmd = command[0]
            if cmd == "quit":
                self.opvServer.stop()
            elif cmd == "clear":
                self.dispArea.clear()
                self.dispArea.refresh()
            elif cmd == "ping":
                print(color.OKBLUE+"ControlTerm : ping",color.ENDC)
                print(color.OKGREEN+"ControlTerm : ping",color.ENDC)
                print(color.WARNING+"ControlTerm : ping",color.ENDC)
                print(color.FAIL+"ControlTerm : ping",color.ENDC)
                print(color.ENDC+"ControlTerm : ping",color.ENDC)
            elif cmd == "geoinfo":
                print("lat :",self.lat,"lon :",self.lon,"alt :",self.alt,"compas :",self.rad)
            elif cmd == "bat":
                print("Battery voltage : ",self.battery_volatge)
            elif cmd == "turnoff":
                if self.opvServer:
                    self.opvServer.turnOff()
                else:
                    print("ControlTerm : Turn off")
            elif cmd == "turnon":
                if self.opvServer:
                    self.opvServer.turnOn()
                else:
                    print("ControlTerm : Turn on")
            elif cmd == "takepic":
                if self.opvServer:
                    self.opvServer.takePic()
                else:
                    print("ControlTerm : Take pic")
            elif cmd == "auto":
                if len(command) >= 2:
                    try:
                        dist = int(command[1])
                    except ValueError:
                        print("ControlTerm : Error : wrong distance")
                    else:
                        dist = math.ceil(dist/5)*5
                        if self.opvServer:
                            self.opvServer.setAuto(frequMetre=dist)
                        else:
                            print("ControlTerm : Setting auto-mode for",dist,"meters")
                else:
                    print("ControlTerm : Distance parameter missing")
            else:
                if cmd != "help":
                    print("Command :",command,"unrecognized")
                print("Here is a list of available command :\n"
                    "auto [dist] : enable automode to take picture every [dist] meters\n"
                    "takepic     : take a picture\n"
                    "turnOn      : turn all GoPro On\n"
                    "turnOff     : turn all GoPro Off\n"
                    "geoInfo     : display geolocalisation information\n"
                    "bat         : display battery voltage\n"
                    "ping        : try it\n"
                    "clear       : clear the screen\n"
                    "help        : display this help\n"
                    "quit        : stop the OPV server\n"
                    )

    #the following methode won't do anything for now

    def canMove(self):
        """
        notify the user that he can move
        """
        pass

    def setGeoInfo(self,lat,lon,alt,rad):
        """
        notify the user of geographical position
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.rad = rad
        #NOTE : We could add a "notification" bar at the top to display time, geoInfo, etc

    def setModeInfo(self,isAutoModeOn,dist):
        """
        notify the user of automode configuration
        """
        #same here, we could display that in a notification barre
        pass

    def setBatteryInfo(self, battery_volatge):
        """Notify the user of battery voltage."""
        self.battery_volatge = battery_volatge

    def notif(self,succes):
        """
        notify the user of a succes/fail in an action
        """
        pass

    def newPanorama(self,succes=True,**kwargs):
        """
        notify the user of new panorama taking
        """
        pass
