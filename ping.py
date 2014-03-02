import os,sys
sys.path.append(os.path.realpath(__file__)[:os.path.realpath(__file__).rfind("/")]+"/includes")

import serial
import time
import threading
import subprocess
import color

ARDUINO_SERIAL = "/dev/ttyUSB0"

EYEFI_IP = ["192.168.42."+str(i) for i in range(100,106)]

def test():

        fail_list = ping(EYEFI_IP)
        if fail_list:
            print(color.WARNING,"SOME CARD DIDN'T ANSWER, NEW PING SESSION",color.ENDC)
            error = ping(fail_list)
        else:
            error = None
        if error:
            print(color.FAIL,"ALL THOSE IP FAILED TO PING TWICE:",color.ENDC)
            for ip in error:
                print(color.FAIL,ip,color.ENDC)
        print(color.ENDC,end="")
        
def ping(ipList):
        """
        ping all ip in the list and tell wich one don't answer
        """
        error = []
        
        
        for ip in ipList:            
            if not subprocess.call("ping -c 1 "+ip,shell=True):
                print(color.OKGREEN,ip,"CONNECTED : OK",color.ENDC)
            else:
                print(color.FAIL,ip,"NOT CONNECTED : ERROR",color.ENDC)
                error.append(ip)
        return error

test()


