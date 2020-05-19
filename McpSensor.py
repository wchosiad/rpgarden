from os import path
import configparser

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
from adafruit_mcp3xxx.analog_in import AnalogIn # handles the sensor

VALUE_RANGE_SIZE = 100 # number of values in our converted moisture range

class McpSensor:
    def __init__(self, mcp, iniFileName, iniSectionName):
        try:
            # set up default values
            self.minVal = 35000
            self.maxVal = 35001
            self.mcp_pin = 0

            # set ini file values
            self.iniFileName = iniFileName
            self.iniSectionName = iniSectionName
            self.sensorSection = None
            self.rpgConfig = None

            # Read in configuration values, if they exist
            # If not, add them to the config file
            self.rpgConfig = configparser.ConfigParser()  # Create ConfigParser object
            if path.exists(self.iniFileName):             # Check to see if ini file exists
                self.rpgConfig.read(self.iniFileName)     # Load its data from the file

            if self.iniSectionName in self.rpgConfig:
                # Read values from ini file
                self.sensorSection = self.rpgConfig[self.iniSectionName]
                self.maxVal = int(self.sensorSection['top'])
                self.minVal = int(self.sensorSection['bottom'])
                self.mcp_pin = int(self.sensorSection['mcp_channel'])
            else:
                # Write values to ini file
                self.rpgConfig.add_section(self.iniSectionName)
                self.sensorSection = self.rpgConfig[self.iniSectionName]
                self.sensorSection["top"] = str(self.maxVal)
                self.sensorSection["bottom"] = str(self.minVal)
                self.sensorSection['mcp_channel'] = str(self.mcp_pin)
                with open(self.iniFileName, 'w') as configfile:
                    self.rpgConfig.write(configfile)
            
            # set up MoistureSensor object
            self.sensor = AnalogIn(mcp, self.mcp_pin)

            # Factor for converting readings to a 0-100 range
            self.factor = float(self.maxVal - self.minVal) / float(VALUE_RANGE_SIZE)

        except Exception as ex:
            # Handle other exceptions
            print(type(ex))
            print(ex.args)
            print(ex)
            raise(ex)

    # Returns raw value
    def read_raw(self):
        foundNewBounds = False
        val = self.sensor.value

        if (val > self.maxVal):
            foundNewBounds = True
            self.maxVal = val
            self.sensorSection['top'] = str(self.maxVal)

        if (val < self.minVal):
            foundNewBounds = True
            self.minVal = val
            self.sensorSection['bottom'] = str(self.minVal)

        if (foundNewBounds):  # Update the ini file
            self.factor = float(self.maxVal - self.minVal) / float(VALUE_RANGE_SIZE)
            with open(self.iniFileName, 'w') as configfile:
                self.rpgConfig.write(configfile)

        return val
    
    # Reads value from sensor and returns value converted to range from 0 to VALUE_RANGE_SIZE
    def read(self):
        return self.convert(self.read_raw())

    # converts raw values to something from 0 to VALUE_RANGE_SIZE
    def convert(self, val):
        return float(val - self.minVal) / self.factor
