from i2clibraries import i2c_hmc5883l


class Compas:
    """A simple class to acces the compas data."""

    def __init__(self, opvServer=None):
        """Init all stuff."""

        self.opvServer = opvServer

        if not self.opvServer.config.get("FAKE_MODE"):
            try:
                self.__hmc5883l = i2c_hmc5883l.i2c_hmc5883l(1)
                self.__hmc5883l.setContinuousMode()
                # used to correct default due to the geometry of earth magnetic field
                self.__hmc5883l.setDeclination(9, 54)
            except OSError:
                print("fake compass")

#    # To get degrees and minutes into variables
#    (degrees, minutes) = hmc5883l.getDeclination()
#    (degress, minutes) = hmc5883l.getHeading()

    def getHeading(self):
        """
        return the heading of the compas
        """
        if self.opvServer.config.get("FAKE_MODE"):
            return b'404\xc2\xb042'.decode("utf-8")
        # return b'404\xc2\xb042'.decode("utf-8")
        return self.__hmc5883l.getHeadingString()

    def getDeclination(self):
        """
        return the declination of the compas
        """
        if self.opvServer.config.get("FAKE_MODE"):
            return "404°42"
        return "404°42"
        # return self.__hmc5883l.getDeclinationString()

if __name__ == "__main__":
    import time
    compas = Compas()
    while 1:
        print(compas.getHeading())
        time.sleep(1)
