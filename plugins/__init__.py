from . import pyWebSocket, LiveViewServer, controlTerm



class Manager(object):
    """
    the manager manage all plugins
    """

    def __init__(self,opvServer):
        """
        init everything
        """

        self.opvServer = opvServer
        self.interfaces = list()

        self.interfaces.append(controlTerm.ControlTerm(self.opvServer))
        self.interfaces.append(pyWebSocket.WebSocketServer(self.opvServer))
        self.interfaces.append(LiveViewServer.LiveViewServer(self.opvServer))        
    
    def __iter__(self):
        """
        to allow the iteration, we only car about interfaces
        """
        return self.interfaces.__iter__()

    def notif(self,succes):
        """
        notify the user of a succes/fail in an action
        """
        for i in self.interfaces:
            i.notif(succes)

    def newPanorama(self,succes=True,**kwargs):
        """
        send information about new panorama
        """
        for i in self.interfaces:
            i.newPanorama(succes=succes,**kwargs)

    def canMove(self):
        """
        inform interface the  user can move
        """
        for i in self.interfaces:
            i.canMove()

    def setGeoInfo(self,lat,lon,alt,rad):
        """
        set current geographical information
        """
        for i in self.interfaces:
            i.setGeoInfo(lat,lon,alt,rad)

    def setModeInfo(self,isAutoModeOn,dist):
        """
        set information about automode
        """
        for i in self.interfaces:
            i.setModeInfo(isAutoModeOn,dist)

    def stop(self):
        """
        stop the interface
        """
        for i in self.interfaces:
            i.stop()

    def __del__(self):
        """
        destroy everything
        """
        for i in self.interfaces:
            i.__del__()

# Plugins must define the following methode : 
# def notif(self,succes)
# def newPanorama(self,succes=True,**kwargs)
# def canMove(self)
# def setGeoInfo(self,lat,lon,alt,rad)
# def setModeInfo(self,isAutoModeOn,dist)
# def stop(self)
# def __del__(self)
# def __init__(self,opvServer)



