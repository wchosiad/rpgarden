"""
RpgConfig and subclasses, SensorConfig, ClockSensorConfig, DhtSensorConfig, and McpSensorConfig:
Provides a facade in front of Python's configparser module to handle configuration persistent settings

WHile there is a singleton parserInstance which holds information regarding the entire config file, an
RpgConfig instance represents a single section within the configparser.  Options within that section can be
read and written using . notation (myConfig.sort, for example).

Any time an option's value is changed, it is immediately saved to the configparser's .ini file.
"""

import configparser
import sys
from os import path
import traceback

class RpgConfig:
    RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"

    # The private file is another configuration file that's not stored in GitHub for holding passwords and 
    # other private info
    # It has one section called: [Private]
    # It's options are accessible as yourRpgConfigVariable.private['your_option_name']
    RPGARDEN_PRIVATE_FILE = "/home/pi/.rpgarden/rpgarden.ini"

    parserInstance = None # We want all updates to go through the class singleton variable, parserInstance
    privateInstance = None # The private file is read-only, as far as this module is concerned

    def __init__(self, sectionName="General", cfgFile=RPGARDEN_CONFIG_FILE):
        # self.configFile = cfgFile              # Initialize instance members
        # self.sectionName = sectionName
        self.__dict__["configFile"] = cfgFile
        self.__dict__["sectionName"] = sectionName
        self.__dict__["section"] = None
        self.__dict__["private"] = None

        if not RpgConfig.parserInstance:                            # If parser hasn't already been initialized
            RpgConfig.parserInstance = configparser.ConfigParser()  # Create ConfigParser object
            RpgConfig.privateInstance = configparser.ConfigParser()  # Create ConfigParser object

            if path.exists(cfgFile):                                # If the ini file exists
                RpgConfig.parserInstance.read(cfgFile)              # Load its data from the file
            else:
                RpgConfig.parserInstance.add_section(sectionName)   # It's a new ini file. Add the section and
                self.save()                                         # Write out the ini file

            # Load up the private config file, if it exists
            if path.exists(RpgConfig.RPGARDEN_PRIVATE_FILE):             # If the PRIVATE ini file exists
                RpgConfig.privateInstance.read(RpgConfig.RPGARDEN_PRIVATE_FILE) # Load its data from the file
                self.__dict__["private"] = RpgConfig.privateInstance['Private']

        if not sectionName in RpgConfig.parserInstance:             # Existing ini file, but new section
            RpgConfig.parserInstance.add_section(sectionName)       # Add the section and save
            self.save()
        
        # After this, changes to self.section will automagically change the original configparser
        self.__dict__["section"] = RpgConfig.parserInstance[sectionName]

    # saves the current state of the entire configparser object to the ini file
    def save(self):
        with open(self.configFile, 'w') as configfile:          # Write out the ini file
            RpgConfig.parserInstance.write(configfile)

    # Sets an option value within the current section if it is different from current value
    # If the new value is not a string type, it also sets an instance variable to the 
    # non-string option
    def set(self, key, value): 
        myKey = str(key)
        # only set the value if it's changed or doesn't exist
        if self.has(myKey):
            if self.section[myKey] != str(value):
                self.section[myKey] = str(value)
                self.save()
        else:
            self.section[myKey] = str(value)
            self.save()

        # if the value passed in was not a string, also save a instance version in the native data type
        if not isinstance(value, str):   # Hold non-string values in an instance variable
            self.__dict__[str(key)] = value

    # Gets a value. First, it looks in self (for non-string versions), then in the configparser's data. 
    def get(self, key, defaultVal=None):
        retVal = defaultVal
        myKey = str(key)
        try:
            if myKey in self.__dict__:
                retVal = self.__dict__[myKey]
            elif self.section and myKey in self.section:
                retVal = self.section[myKey]
        except Exception as ex:
            print(traceback.format_exc())

        return retVal
    
    # returns True if the key is an option in the configparser
    def has(self, key):
        return (str(key) in self.section)

    # pass-through to the configparser's function
    def getboolean(self, key, defaultVal=None): 
        retVal = RpgConfig.parserInstance.getboolean(self.sectionName, str(key), fallback=defaultVal)
        return retVal

    # pass-through to the configparser's function
    def getint(self, key, defaultVal=None): 
        retVal = RpgConfig.parserInstance.getint(self.sectionName, str(key), fallback=defaultVal)
        return retVal

    # pass-through to the configparser's function
    def getfloat(self, key, defaultVal=None): 
        retVal = RpgConfig.parserInstance.getfloat(self.sectionName, str(key), fallback=defaultVal)
        return retVal

    # Given the section Name, returns the type of sensor
    def getSensorType(self, iniSectionName, defaultVal=None):
        return RpgConfig.parserInstance.get(iniSectionName, "type", fallback=defaultVal)
    
    # Gets an attribute from the configparser object using dot notation.  Only called if the 
    # attribute isn't already one of this objects properties
    def __getattr__(self, key):
        return self.get(key)

    # Sets an attribute on the configparser object using dot notation.
    def __setattr__(self, key, value):
        self.set(key, value)


# SensorConfig: Base class for all Sensor-related Config objects
class SensorConfig(RpgConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)

        # Make sure we have all the non-string and required values
        self.sort = self.getint('sort', defaultVal=50)
        self.type = self.get('type', defaultVal="generic")
        self.description = self.get('description', defaultVal="Generic Sensor")
        self.field_name = self.get('field_name', defaultVal="generic")

# ClockSensorConfig: Configuration for "pretend" clock sensor
class ClockSensorConfig(SensorConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)

        # Make sure we have all the required values
        self.clock_format = self.get('clock_format', defaultVal="%%Y-%%m-%%d %%H:%%M:%%S")

# DhtSensorConfig: Configuration for Temperature and humidity sensor
class DhtSensorConfig(SensorConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)
        #cfg = RpgConfig.parserInstance 

        # Make sure we have all the non-string and required values
        self.pin = self.getint('pin')
        self.dht_type = self.get('dht_type')
        self.scale = self.get('scale')

# McpSensorConfig: Configuration for Soil Moisture sensors and photo-resistor light sensors
class McpSensorConfig(SensorConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)

        # Make sure we have all the non-string values
        self.maxVal = self.getint('top', defaultVal=35000)
        self.minVal = self.getint('bottom', defaultVal=35001)
        self.mcp_pin = self.getint('mcp_channel', defaultVal=0)
        self.reverse = self.getboolean('reverse', defaultVal=False)
        self.calibrated = self.getboolean('calibrated', defaultVal=False)
