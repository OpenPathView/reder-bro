import socket, threading, hashlib, base64, select
import color

SOCKET_PORT = 9876

class WebSocketServer(threading.Thread):
    """
    A server receiving connection for websocket
    """
    
    def __init__(self,opvServer=None):
        """
        init the WebSocket Server, receiveHandler, if given, is called when a socket receive data with socket as first parameter and msg as second one
        """
        print(color.OKBLUE+"Initializing WebSocket server...",color.ENDC)
        threading.Thread.__init__(self)
        self.opvServer = opvServer
        self.daemon = True
        self.receiveHandler=self.opvServer.socketHandler if self.opvServer else None
        self.panoramas = []   #keep all taken panorama so that we can keep track when opening a new page
        try:
            with open("picturesInfo.csv") as picFile:
                picFile.readline()
                for index,line in enumerate(picFile.readlines()):
                    try:
                        line=line.split(";")                    
                        lat=line[1]
                        lon=line[2]
                        alt=line[3]
                        rad=line[4]
                        msg="""{"pano" : {"lat": "%F", lon:"%F", alt:"%F", rad:"%s"}}"""\
                                    %(lat,lon,alt,rad)
                        self.panoramas.append(msg)
                    except Exception as e:
                        print(color.WARNING,"Line %i malformed : %s"%(index,e),color.ENDC)            
        except Exception:
            print(color.WARNING,"File not found or malformed file",color.ENDC)


        self.__webSock = socket.socket()
        self.__webSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__webSock.bind(('', SOCKET_PORT))
        self.__webSock.listen(5)
        self.client = []
        self.keepAlive = threading.Event()        
        self.start()
        print(color.OKGREEN+"WebSocket server initialized",color.ENDC)

    def __del__(self):
        """
        destructor
        """
        print(color.WARNING+"destroying WebSocket",color.ENDC)

    def stop(self):
        """
        stop the thread
        """
        print(color.OKBLUE+"Stopping WebSocket Thread...",color.ENDC)
        self.keepAlive.clear()
        print(color.OKGREEN+"WebSocket Thread stopped",color.ENDC)
    
    def run(self):
        """
        a thread receiving incoming websocket connection
        """
        self.keepAlive.set()

        while self.keepAlive.isSet():
            readable, writable, errors = select.select([self.__webSock],[],[])
            if readable == [self.__webSock]:
                conn, address = self.__webSock.accept()
                newClient = WebSocketClient(conn, address, self.receiveHandler)
                self.client.append(newClient)
                for p in self.panoramas:
                    newClient.send(p)
                    
    def setGeoInfo(self,lat,lon,alt,rad):
        """
        notify the user of geographical position
        """
        msg='{"pos":{"lat":%f, "long":%f, "alt":%f "rad":"%s"}}'%(lat,lon,alt,rad.replace("°"," deg"))      
        self.send2All(msg) 

    def setModeInfo(self,isAutoModeOn,dist):
        """
        notify the user of automode configuration
        """
        msg="""{"config":{"auto":"%s","dist":"%i"}}"""%(str(isAutoModeOn),dist)
        self.send2All(msg)

    def newPanorama(self,succes=True,**kwargs):
        """
        notify the user of new panorama taking
        """
        if succes:
            lat = kwargs["latitude"]
            lon = kwargs["longitude"]
            alt = kwargs["altitude"]
            rad = kwargs["heading"]
            msg="""{"pano" : {"lat": "%F", lon:"%F", alt:"%F", rad:"%s"}}"""%(lat,lon,alt,rad)
            self.send2All(msg)

    def notif(self,succes):
        """
        notify the user of a succes/fail in an action
        """
        self.send2All("""{"succes":%s}"""%("true" if succes else "false"))

    def canMove(self):
        """
        notify the user that he can move
        """
        pass
    
    def send2All(self,msg):
        """
        send a message to all opened client webSocket
        """

        for index, client in enumerate(self.client) :
            try:
                client.send(msg)
            except socket.error :
                self.client.pop(index)    

class WebSocketClient(threading.Thread):
    """
    A single connection (client) of the program
    """
    
    def __init__(self, sock, addr, receiveHandler=None):
        """
        init the client connection
        if given, receivHandler will be called when the socket received a message
        """        
        threading.Thread.__init__(self)
        self.daemon = True
        self.__sock = sock
        self.addr = addr
        self.keepAlive = True
        self.__receivedData = []
        self.handshake()
        self.receiveHandler = receiveHandler
        self.start()
        
    def handshake(self):
        """
        handshake the client
        """
        data = self.__sock.recv(1024).decode("ascii") #get the connection request

        print(data)
        
        data = data.split("\r\n")
        for i in data:
            if "Sec-WebSocket-Key" in i:
                break
                
        i = i.encode("ascii")+b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        hasher = hashlib.sha1()        
        key1 = i[len("Sec-WebSocket-Key: "):]
        hasher.update(key1)        
        key = base64.b64encode(hasher.digest()).decode("utf-8")
        handshake = "HTTP/1.1 101 Web Socket Protocol Handshake\r\nUpgrade: WebSocket\r\nConnection: Upgrade\r\nWebSocket-Protocol: chat\r\nSec-WebSocket-Accept: "+str(key)+"\r\n\r\n"
        print(handshake)
        self.__sock.send(handshake.encode())
        
    def run(self):
        """
        keep receiving data from the webSocket
        """

        while self.keepAlive:
            data = self.__sock.recv(1024)
            if not data: break
            self.__onreceive(data)

    def send(self, msg):
        """
        Send a message to this client
        """
        
        bytesFormatted=bytearray()
        bytesFormatted.append(129)
        
        indexStartRawData = -1

        if len(msg) <= 125:
            bytesFormatted.append(len(msg))
            indexStartRawData = 2

        elif len(msg) >= 126 and len(msg) <= 65535:
            bytesFormatted.append(126)
            bytesFormatted.append((len(msg) >> 8) & 255)
            bytesFormatted.append((len(msg)     ) & 255)
            indexStartRawData = 4

        else:
            bytesFormatted.append(127)
            bytesFormatted.append((len(msg) >> 56) & 255)
            bytesFormatted.append((len(msg) >> 48) & 255)
            bytesFormatted.append((len(msg) >> 40) & 255)
            bytesFormatted.append((len(msg) >> 32) & 255)
            bytesFormatted.append((len(msg) >> 24) & 255)
            bytesFormatted.append((len(msg) >> 16) & 255)
            bytesFormatted.append((len(msg) >>  8) & 255)
            bytesFormatted.append((len(msg)      ) & 255)
            indexStartRawData = 10

        # put raw data
        for val in msg:
            bytesFormatted.append(ord(val))
            
        self.__sock.send(bytesFormatted)

    def __onreceive(self, data):
        """
        Event called when a message is received from this client
        """

        secondByte = data[1]
        length = secondByte&127 # may not be the actual length in the two special cases

        indexFirstMask = 2 # if not a special case

        if length == 126: # the lenght is coded on two more bytes
            indexFirstMask = 4
        elif length == 127: # the lenght is coded on eight more bytes 
            indexFirstMask = 10 
            
        masks = data[indexFirstMask:indexFirstMask+4] # four bytes starting from indexFirstMask

        indexFirstDataByte = indexFirstMask + 4 # four bytes further

        decoded = '' #contain the decoded message

        j = 0
        for i in range(indexFirstDataByte,len(data)):
            unmasked = data[i]^masks[j%4] # the ^ is a xor
            decoded+=chr(unmasked)
            j+=1                        
        
        self.__receivedData.append(decoded)
        if self.receiveHandler:
            self.receiveHandler(self,decoded)
        else:
            print(decoded)
        
    def getData(self):
        """
        return the elder received data
        """
        return self.__receivedData.pop(0)
        
        
if __name__=="__main__":
    webSocketServer = WebSocketServer()
    webSocketServer.join()

















        
