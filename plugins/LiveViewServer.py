#!/usr/bin/python3


# Copyright (c) 2011, Andrew de Quincey
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from . import LiveViewMessages
import sys
import time
import socket
import threading
import color

LIVEVIEW_MAC = '30:39:26:C4:B0:C2' # The MAC address of the LiveView Watch
#LIVEVIEW_MAC = " 30:39:26:C4:B1:9B" #benvii's watch

MANU_MENU_ID = 0
AUTO_MENU_ID = 1
INFO_MENU_ID = 2
ON_MENU_ID = 3
OFF_MENU_ID = 4


class LiveViewServer(threading.Thread):
    """
    manageLiveView connexion and actions
    """
    
    def __init__(self,osvServer=None,debug = False):
        """
        init the server, loading needed componant
        """
        print(color.OKBLUE+"Initializing LiveView server...",color.ENDC)
        threading.Thread.__init__(self)
        self.daemon = True
        self.debug = debug


 
        self.lat = 0
        self.lon = 0
        self.alt = -42
        self.rad = 0

        self.menuItems = []
        with open("res/Manu.png","rb") as pngFile:
            self.manuPng = pngFile.read()
            
        with open("res/AutoOn.png","rb") as pngFile:
            self.autoOnPng = pngFile.read()

        with open("res/AutoOff.png","rb") as pngFile:
            self.autoOffPng = pngFile.read()
            
        with open("res/Info.png","rb") as pngFile:
            self.infoPng = pngFile.read()
            
        with open("res/On.png","rb") as pngFile:
            self.onPng = pngFile.read()
            
        with open("res/Off.png","rb") as pngFile:
            self.offPng = pngFile.read()   

        self.clientSocket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        
        self.osvServer=osvServer
        if self.osvServer:
            self.autoModeOn = self.osvServer.isAutoMode()
            self.autoModeDist = self.osvServer.distPhoto
        else:
            self.autoModeOn = False
            self.autoModeDist = 0

        self.keepAlive = threading.Event()
        self.start()
        print(color.OKGREEN+"LiveView server initialized",color.ENDC)

    def __del__(self):
        """
        destructor
        """
        print(color.WARNING+"destroying LiveView Server",color.ENDC)
            
    def setAutoModeConf(self):
        """
        set the autoMode configuration in the osvServer if given
        """
        if self.osvServer:
            self.osvServer.setAuto(frequMetre=self.autoModeDist)
            if self.autoModeOn == False:
                self.osvServer.setAuto() #disable automode
            self.osvServer.updateAllConfigInfo()
        else:
            print("Setting auto mode conf :",self.autoModeDist,"AutoMode :","On" if self.autoModeOn else "Off")
                        
    def connect(self):
        """
        init a connexion with the watch
        """
        self.clientSocket.connect((LIVEVIEW_MAC,1))
        self.clientSocket.send(LiveViewMessages.EncodeGetCaps())
        self.clientSocket.send(LiveViewMessages.EncodeSetVibrate(0, 500))
        time.sleep(0.75)
        self.clientSocket.send(LiveViewMessages.EncodeSetVibrate(0, 250))
        time.sleep(0.5)
        self.clientSocket.send(LiveViewMessages.EncodeSetVibrate(0, 500))
        
    def disconnect(self):
        """
        close the connexion with the watch
        """
        self.clientSocket.close()
        self.clientSocket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        
    def initMenu(self):
        """
        give the watch menu information
        """
        self.clientSocket.send(LiveViewMessages.EncodeGetMenuItemResponse(MANU_MENU_ID, False, 0, "Manu", self.manuPng))

        if self.autoModeOn:
            self.clientSocket.send(LiveViewMessages.EncodeGetMenuItemResponse(AUTO_MENU_ID, True, 0, "AutoOn", self.autoOnPng)) 
        else:
            self.clientSocket.send(LiveViewMessages.EncodeGetMenuItemResponse(AUTO_MENU_ID, True, 0, "AutoOff", self.autoOffPng)) 

        self.clientSocket.send(LiveViewMessages.EncodeGetMenuItemResponse(INFO_MENU_ID, True, 0, "Info", self.infoPng)) 

        self.clientSocket.send(LiveViewMessages.EncodeGetMenuItemResponse(ON_MENU_ID, False, 0, "On", self.onPng))
        self.clientSocket.send(LiveViewMessages.EncodeGetMenuItemResponse(OFF_MENU_ID, False, 0, "Off", self.offPng))        

    def setGeoInfo(self,lat,lon,alt,rad):
        """
        notify the user of geographical position
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.rad = rad

    def newPanorama(self,succes=True,**kwargs):
        """
        notify the user of new panorama taking
        """
        self.notif(succes)

    def setModeInfo(self,isAutoModeOn,dist):
        """
        notify the user of automode configuration
        """
        self.autoModeOn = isAutoModeOn
        self.autoModeDist = dist

        self.clientSocket.send(LiveViewMessages.EncodeSetMenuSize(0))                                                        
        self.clientSocket.send(LiveViewMessages.EncodeClearDisplay())
        self.clientSocket.send(LiveViewMessages.EncodeSetMenuSize(5))        

    def canMove(self):
        """
        send a vibration to tell we can move
        """
        try:
            self.clientSocket.send(LiveViewMessages.EncodeSetVibrate(0, 250))
        except socket.error:
            print(color.FAIL+"Error, socket unavailable",color.ENDC)          

    def notif(self,succes):
        """
        notify the user of a succes/fail in an action
        """
        try:
            if succes:
                self.clientSocket.send(LiveViewMessages.EncodeSetVibrate(0, 500))
            else:
                self.clientSocket.send(LiveViewMessages.EncodeSetVibrate(0, 5000))
        except socket.error:
            print(color.FAIL+"Error, socket unavailable",color.ENDC)        

    def stop(self):
        """
        stop the thread
        """
        print(color.OKBLUE+"Stopping LiveView Thread...",color.ENDC)
        self.keepAlive.clear()
        print(color.OKGREEN+"LiveView Thread stopped",color.ENDC)

    def run(self):
        """
        main thread loop
        """
        self.keepAlive.set()
        lastFail = None
        while self.keepAlive.isSet():        
            try:                    #Try to connect the watch
                if not self.debug:
                    self.connect()
                else:
                    time.sleep(1)                
            except socket.error as e:
                if str(lastFail)!=str(e):
                    lastFail=e
                    print(color.WARNING+"Connexion failed",e,color.ENDC)
                self.disconnect()
                continue            #If the connection fail we keep trying                                
            try :                   #a try statement allow prevent crash in case of disconnect
                menu = None    
                while True:
                    for msg in LiveViewMessages.Decode(self.clientSocket.recv(4096)):
                        # Handle result messages
                        if isinstance(msg, LiveViewMessages.Result):
                            if msg.code != LiveViewMessages.RESULT_OK:
                                print("---------------------------- NON-OK RESULT RECEIVED ----------------------------------")
                                print(msg)
                            continue
                        # Handling for all other messages
                        self.clientSocket.send(LiveViewMessages.EncodeAck(msg.messageId))
                        if isinstance(msg, LiveViewMessages.GetMenuItems):
                            self.initMenu()
                        elif isinstance(msg, LiveViewMessages.GetMenuItem):
                            print("---------------------------- GETMENUITEM RECEIVED ----------------------------------")
                            # FIXME: do something!

                        elif isinstance(msg, LiveViewMessages.DisplayCapabilities):
                            deviceCapabilities = msg                           
                            self.clientSocket.send(LiveViewMessages.EncodeSetMenuSize(5))
                            self.clientSocket.send(LiveViewMessages.EncodeSetMenuSettings(5, 0))
                        elif isinstance(msg, LiveViewMessages.GetTime):
                            self.clientSocket.send(LiveViewMessages.EncodeGetTimeResponse(time.time(), True))
                        elif isinstance(msg, LiveViewMessages.DeviceStatus):
                            self.clientSocket.send(LiveViewMessages.EncodeDeviceStatusAck())
                        elif isinstance(msg, LiveViewMessages.GetAlert):                               
                            if msg.menuItemId == AUTO_MENU_ID:
                                menu = AUTO_MENU_ID
                                if msg.alertAction == LiveViewMessages.ALERTACTION_FIRST:
                                    autoModeDist = self.autoModeDist
                                    autoModeOn = self.autoModeOn
                                if msg.alertAction == LiveViewMessages.ALERTACTION_PREV:
                                    if autoModeDist>=0:
                                        autoModeDist-=5                                    
                                elif msg.alertAction == LiveViewMessages.ALERTACTION_NEXT:
                                    if autoModeDist<30:
                                        autoModeDist+=5                                       
                                if autoModeDist%5!=0:
                                    autoModeDist-=autoModeDist%5                                
                                if autoModeDist<=0:
                                    autoModeDist = 0
                                    autoModeOn = False
                                else:
                                    autoModeOn = True                                    
                                if autoModeOn:
                                    self.clientSocket.send(LiveViewMessages.EncodeGetAlertResponse(7, 7, int(autoModeDist/5), "Auto Mode", "Configuration", "Prise de vue tout les : "+str(autoModeDist)+"m", self.autoOnPng))
                                else:
                                    self.clientSocket.send(LiveViewMessages.EncodeGetAlertResponse(7, 7, 0, "Auto Mode", "Configuration", "Mode auto desactive", self.autoOffPng))
                            elif msg.menuItemId == INFO_MENU_ID:
                                menu = INFO_MENU_ID
                                self.clientSocket.send(LiveViewMessages.EncodeGetAlertResponse(1, 1, 0, "GeoLocalisation", "Information", "lat %f\nlon %f\nheading %s"%(self.lat,self.lon,self.rad), self.autoOnPng))
                        elif isinstance(msg, LiveViewMessages.Navigation):
                            if msg.navType == LiveViewMessages.NAVTYPE_SELECT:
                                menu = None
                            if menu == AUTO_MENU_ID:
                                if msg.navType == LiveViewMessages.NAVTYPE_MENUSELECT:
                                    self.autoModeDist=autoModeDist
                                    self.autoModeOn=autoModeOn
                                    self.setAutoModeConf()
                                    if self.autoModeOn:
                                        print(color.OKBLUE+"auto mode set",color.ENDC)
                                    else:
                                        print(color.OKBLUE+"auto mode unset",color.ENDC)                            
                            if msg.wasInAlert == False:
                                if msg.menuItemId == MANU_MENU_ID:
                                    if self.osvServer:
                                        self.osvServer.takePic()
                                    else:
                                        print("Take pic")
                                elif msg.menuItemId == ON_MENU_ID:
                                    if self.osvServer:
                                        self.osvServer.turnOn()
                                    else:
                                        print("Turn on")
                                elif msg.menuItemId == OFF_MENU_ID:
                                    if self.osvServer:
                                        self.osvServer.turnOff()
                                    else:
                                        print("Turn off")                                    
                            self.clientSocket.send(LiveViewMessages.EncodeNavigationResponse(LiveViewMessages.RESULT_EXIT))                                        
                            self.clientSocket.send(LiveViewMessages.EncodeClearDisplay())

            except socket.error as e:
                print(color.WARNING+"Connexion lost :",e,color.ENDC)                        

if __name__=="__main__":
    serv = LiveViewServer()
    serv.join()                       
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                

