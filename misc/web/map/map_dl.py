import math
import urllib.request
import os, sys

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[00m'

scriptDir = os.path.dirname(sys.argv[0])
if scriptDir:
    os.chdir(scriptDir)


print(sys.argv[0])

def x2deg(xtile, zoom):
    n = 2.0 ** zoom
    lon_deg_min =  - 180.0 + xtile / n * 360.0
    lon_deg_max =  - 180.0 + (xtile+1) / n * 360.0
    return lon_deg_min,lon_deg_max

def y2deg(ytile, zoom):
    n = 2.0 ** zoom
    lat_deg_max = 85.0511-(170.1022*(ytile/n))
    lat_deg_min = 85.0511-(170.1022*((ytile+1)/n))
    return lat_deg_min, lat_deg_max

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

nbrLoaded = 0


def checkAndLoad(x,y,z):

    addr = "http://a.tile.openstreetmap.org/{z}/{x}/{y}.png".format(z=z,x=x,y=y)

    pathName = "%i/%i/"%(z,x)
    fileName = "%i.png"%(y)
    if not os.path.exists(pathName):
        os.makedirs(pathName)
    if os.path.exists(pathName+fileName):
        print(OKBLUE+"Already downloaded"+ENDC,x,y,z)
        return
    else:
        global nbrLoaded
        nbrLoaded +=1
        ok = False
        print("Downloading",x,y,z,"...",end="")
        while not ok:
            try:
                response = urllib.request.urlopen(addr)
            except (Exception) as e:
                print(e)
            else:
                ok=True
            print(".",end="")    
        html = response.read()
        with open(pathName+fileName,"wb") as fileName:
            fileName.write(html)
        print(OKGREEN+"DONE"+ENDC)

left = -5.537
top =   50.121
right = -0.791
bottom = 46.860

zoom_min = 0
zoom_max = 13


for z in range(zoom_min,zoom_max+1):

    x_min, y_max = deg2num(left, bottom, z)    
    x_max, y_min = deg2num(right, top, z)    

    x_min-=1
    y_min-=1

    y_max+=1
    x_max+=1

    print("x from [%i to %i["%(x_min,x_max))
    print("y from [%i to %i["%(y_min,y_max))

    for x in range(x_min,x_max):
        for y in range(y_min,y_max):
            checkAndLoad(x%(2**z),y%(2**z),z)

    # for x in range(x_min,x_max):
    #     lon, lonn = x2deg(x,z)
    #     if lon<=top<=lonn or lon<=bottom<=lonn or top>=lon>=bottom or top>=lonn>=bottom:
    #         for y in range(y_min,y_max):
    #             lat, latn = y2deg(y,z)
    #             if lat<=left<=latn or lat<=right<=latn or left<=lat<=right or left<=latn<=right:
    #                 checkAndLoad(x,y,z)

print("loaded :",nbrLoaded)