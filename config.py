import configparser, os
import color
from ast import literal_eval
class Config(object):
    """
    define a configuration, as it's an object, it will be the same for all plugins
    """

    def __init__(self):
        """
        initial configuration
        """
        print(color.OKBLUE+"Loading configuration file...",color.ENDC)

        path = os.path.dirname(os.path.realpath(__file__))
        if not os.path.isfile(os.path.join(path,"config.ini")):
            print(color.WARNING,"Configuration file not found",color.ENDC)
            return

        cp = configparser.ConfigParser()
        cp.read(os.path.join(path,"config.ini"))

        self.settings = dict()
        for section in cp:
            print(color.OKBLUE+"loading section %s"%(section),color.ENDC)
            try:
                self.settings.update(cp.items(section))                
            except Exception as e:
                print(color.FAIL+"Error reading the section : %s"%(e),color.ENDC)

        print("Loaded the following settings : ")
        for k,v in self.settings.items():
            print("\t%s"%(k))
            self.settings[k] = literal_eval(v)
        print(color.OKGREEN+"Configuration loaded",color.ENDC)

    def get(self,param):
        """
        return requested config parameters if exist, else None
        """
        param = param.lower()
        if param in self.settings:
            return self.settings[param]
        else:
            return None

    def set(self,param,value):
        """
        set a parameters value
        """
        self.settings[param]=value

if __name__ == "__main__":
    c = Config()
