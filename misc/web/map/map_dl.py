import math
import urllib.request
import os

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    # xtile = int(n * ((lon_deg + 180.0) / 360.0))
    # ytile = int(n * ((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0) )
    xtile = int(((lon_deg + 180)/360) * n)    
    ytile = int(((lat_deg + 85.0511)/(2*85.0511)) * n) 
    return (xtile, ytile)


nbrLoaded = 0


def checkAndLoad(x,y,z):

    addr = "http://a.tile.openstreetmap.org/{z}/{x}/{y}.png".format(z=z,x=x,y=y)

    pathName = "%i/%i/"%(z,x)
    fileName = "%i.png"%(y)
    if not os.path.exists(pathName):
        os.makedirs(pathName)
    if os.path.exists(pathName+fileName):
        return
    else:
        global nbrLoaded
        nbrLoaded +=1
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

left = -4.7804
top =   48.6837
right = -4.2091
bottom = 48.3316

zoom_min = 0
zoom_max = 13


for z in range(zoom_min,zoom_max+1):


    x_min, y_min = deg2num(left, bottom, z)

    x_max, y_max = deg2num(right, top, z)
    print("x from %i to %i"%(x_min,x_max))
    print("y from %i to %i"%(y_min,y_max))

    if x_min>0:x_min-=1

    for x in range(x_min,x_max+1):
        for y in range(y_min,y_max+1):
            checkAndLoad(x,y,z)



print("loaded :",nbrLoaded)
