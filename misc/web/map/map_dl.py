import math
import urllib.request
import os

def deg2num(lon_deg,lat_deg, zoom):
    n = 2.0 ** zoom
    xtile = int( ((lon_deg + 180.0)/360.0) * n )
    ytile = int( ((lat_deg +  85.0511)/( 85.0511*2)) * n )
    return (xtile, ytile)



def checkAndLoad(x,y,z):

    addr = "http://a.tile.openstreetmap.org/{z}/{x}/{y}.png".format(z=z,x=x,y=y)

    pathName = "%i/%i/"%(z,x)
    fileName = "%i.png"%(y)
    if not os.path.exists(pathName):
        os.makedirs(pathName)
    if os.path.exists(pathName+fileName):
        return 0
    else:
        ok = False
        while not ok:
            try:
                response = urllib.request.urlopen(addr)
            except (Exception) as e:
                print(e)
            else:
                ok=True    
        html = response.read()
        with open(pathName+fileName,"wb") as fileName:
            fileName.write(html)
        return 1

left = -4.7832
top =   48.5780
right = -4.0780
bottom = 48.2544

zoom_min = 0
zoom_max = 13



for z in range(zoom_min,zoom_max+1):
    x_min, y_min = deg2num(left, bottom, z)
    x_max, y_max = deg2num(right, top, z)

    c_range = 2**z 


    x_min-=4
    x_max+=4
    y_min-=4
    y_max+=4

    print("\n"*2)
    print("\n================================"*3)
    print("Zoom = %i"%(z))
    print("x from %i to %i"%(x_min,x_max))
    print("y from %i to %i"%(y_min,y_max))
    print("================================\n"*3)
    print("\n")

    for x in range(x_min,x_max):
        for y in range(y_min,y_max):
            print("Downloading (%i,%i)... "%(x,y),end="")
            r = checkAndLoad(x%c_range,y%c_range,z)
            if r: print("downloaded")
            else: print("already downloaded")
