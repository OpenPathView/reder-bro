import sys, time,os
import color
import threading

class Tee(object):
    """
    Allow to save data in a log file as they are printed
    """
    
    def __init__(self,logFile,mode,screenOut=sys.stdout):
        """
        init everything
        """
        self.stdoutBak = sys.stdout
        self.stderrBak = sys.stderr
        self.logFile = open(logFile,mode)
        self.stdout = screenOut
        sys.stdout = self
        sys.stderr = self
        self.beginNewLine = True
        self.__writeLock = threading.Lock()
        self.__flushLock = threading.Lock()


    def write(self,data):
        """
        write data in the file and in the terminal
        """
        self.__writeLock.acquire()
        endWithCR=False
        if len(data)>=1:
            if data[-1]=="\n":
                endWithCR=True
                data=data[:-1]
        if self.beginNewLine:
            data = "\n"+data
        data = data.replace("\n","\n"+"[{0.tm_mday:=#02}/{0.tm_mon:=#02}/{0.tm_year} {0.tm_hour:=#02}:{0.tm_min:=#02}'{0.tm_sec:=#02}s] ".format(time.localtime()))        
        self.beginNewLine=endWithCR
        self.logFile.write(data)
        self.stdout.write(data)
        self.flush()
        self.__writeLock.release()

    def __del__(self):
        """
        restore everything
        """
        print(color.WARNING+"Closing Tee...",color.ENDC)
        sys.stdout = self.stdoutBak
        sys.stderr = self.stderrBak
        self.logFile.close()        
        print(color.WARNING+"Tee closed",color.ENDC)


    def flush(self):
        """
        flush data
        """
        self.__flushLock.acquire()
        self.logFile.flush()
        self.stdout.flush()
        self.__flushLock.release()


