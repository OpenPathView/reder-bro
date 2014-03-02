#!/usr/bin/python3

import sys
import time
import socket
import threading
import color
import select

SOCKET_PORT = 12345

class AndroidServer(threading.Thread):
    """
    manage android connexion and actions
    """
    
    def __init__(self,osvServer=None,debug = False):
        """
        init the server, loading needed componant
        """
        print(color.OKBLUE+"Initializing AndroidServer server...",color.ENDC)
        threading.Thread.__init__(self)
        self.daemon = True
        self.debug = debug
        
        self.clientSocket = socket.socket()
        self.clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientSocket.bind(('', SOCKET_PORT))
        self.clientSocket.listen(5)

        self.clientConnection = []

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
        print(color.WARNING+"destroying AndroidServer Server",color.ENDC)

    def setGeoInfo(self,lat,lon,alt,rad):
        """
        notify the user of geographical position
        """
        pass

    def newPanorama(self,succes=True,**kwargs):
        """
        notify the user of new panorama taking
        """
        pass

    def setModeInfo(self,isAutoModeOn,dist):
        """
        notify the user of automode configuration
        """
        self.autoModeOn = isAutoModeOn
        self.autoModeDist = dist
        # TO COMPLET

    def canMove(self):
        """
        send a vibration to tell we can move
        """
        try:
            pass
        except socket.error:
            pass          

    def notif(self,succes):
        """
        notify the user of a succes/fail in an action
        """
        try:
            if succes:
                pass
            else:
                pass
        except socket.error:
            pass        

    def stop(self):
        """
        stop the thread
        """
        print(color.OKBLUE+"Stopping AndroidServer Thread...",color.ENDC)
        self.keepAlive.clear()
        print(color.OKGREEN+"AndroidServer Thread stopped",color.ENDC)

    def run(self):
        """
        main thread loop
        """
        self.keepAlive.set()
        while self.keepAlive.isSet():
            lReadable = [self.clientSocket]+self.clientConnection
            readable, writable, errors = select.select(lReadable,[],[])
            if readable == [self.clientSocket]:
                conn, address = self.clientSocket.accept()
                print(color.OKBLUE+"New connection from Android :",address,color.ENDC)
                self.clientConnection.append(conn)
            elif set(readable).issubset(set(self.clientConnection)):
                deadSocket = []
                for client in readable:
                    cmd = client.recv(2048).decode("ascii").replace("\n","")
                    if cmd == "":
                        print("Dead connexion :",client)
                        deadSocket.append(client)
                    elif cmd == "ON":
                        if self.osvServer:
                            self.osvServer.turnOn()
                        else:
                            print("Turn on")
                    elif cmd == "OFF":
                        if self.osvServer:
                            self.osvServer.turnOff()
                        else:
                            print("Turn off")
                    elif cmd == "TAKEPIC":
                        if self.osvServer:
                            self.osvServer.takePic()
                        else:
                            print("Take pic")
                for c in deadSocket:
                    self.clientConnection.pop(self.clientConnection.index(c))

if __name__=="__main__":
    serv = AndroidServer()
    serv.join()                       
                                
                                
                                
                                
                                
                                
                                
                                
                                
                                

