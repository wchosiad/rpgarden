import configparser
from os import path

class RpgConfig:
    RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"
    parserInstance = None # We want all updates to go through the class singleton variable, parserInstance

    def __init__(self, sectionName="General", cfgFile=RPGARDEN_CONFIG_FILE):
        self.configFile = cfgFile              # Initialize instance members
        self.sectionName = sectionName

        if not RpgConfig.parserInstance:
            RpgConfig.parserInstance = configparser.ConfigParser()  # Create ConfigParser object

        if path.exists(cfgFile):                                # Check to see if ini file exists
            RpgConfig.parserInstance.read(cfgFile)              # Load its data from the file
        else:
            RpgConfig.parserInstance.add_section(sectionName)   # New file. Add the section
            self.save()                                         # Write out the ini file

        if sectionName in RpgConfig.parserInstance:             # Load the section's variables into the vals dictionary
            self.vals = RpgConfig.parserInstance[sectionName]
        else:
            RpgConfig.parserInstance.add_section(sectionName)   # Add the section if it's not there
            self.vals = {}
            self.save()

    def save(self):
        with open(self.configFile, 'w') as configfile:          # Write out the ini file
            RpgConfig.parserInstance.write(configfile)

    def set(self, key, value): 
        RpgConfig.parserInstance.set(self.sectionName, str(key), str(value))
        self.save()

    def get(self, key): 
        retVal = RpgConfig.parserInstance.get(self.sectionName, str(key), fallback=None)
        return retVal

    def getboolean(self, key): 
        return RpgConfig.parserInstance.getboolean(self.sectionName, str(key), fallback=None)

    def getint(self, key): 
        return RpgConfig.parserInstance.getint(self.sectionName, str(key), fallback=None)

    def getfloat(self, key): 
        return RpgConfig.parserInstance.getfloat(self.sectionName, str(key), fallback=None)

    def getSensorType(self, iniSectionName):
        return RpgConfig.parserInstance.get(iniSectionName, "type")


# SensorConfig: Base class for all Sensor-related Config objects
class SensorConfig(RpgConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)

        cfg = RpgConfig.parserInstance
        self.cfg = cfg

        if (len(self.vals) == 0):
            self.set("sort","50")
            self.set("type","Unknown")
            self.set("description","Generic Sensor")
            self.set("field_name","sensor")
            self.vals = cfg[self.sectionName]

        self.sort = cfg.getint(sectionName, 'sort')
        self.type = cfg.get(sectionName, 'type')
        self.description = cfg.get(sectionName, 'description')
        self.field_name = cfg.get(sectionName, 'field_name')

# ClockSensorConfig: Configuration for "pretend" clock sensor
class ClockSensorConfig(SensorConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)
        cfg = RpgConfig.parserInstance

        if (len(self.vals) == 4):
            self.set("format","%Y-%m-%d %H:%M:%S")   # "2020-06-16 15:22:55"
            self.vals = cfg[self.sectionName]

        self.format = cfg.get(sectionName, 'format')

# DhtSensorConfig: Configuration for Temperature and humidity sensor
class DhtSensorConfig(SensorConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)
        cfg = RpgConfig.parserInstance 

        if (len(self.vals) == 4):
            self.set("pin","16")
            self.set("dht_type","DHTXX.DHT22")
            self.set("scale","DHTXX.FAHRENHEIT")
            self.vals = cfg[self.sectionName]

        self.pin = cfg.getint(sectionName, 'pin')
        self.dht_type = cfg.get(sectionName, 'dht_type')
        self.scale = cfg.get(sectionName, 'scale')

# McpSensorConfig: Configuration for Soil Moisture sensors and photo-resistor light sensors
class McpSensorConfig(SensorConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)

        cfg = RpgConfig.parserInstance

        if (len(self.vals) == 4):
            self.set("top","35000")
            self.set("bottom","35001")
            self.set("mcp_channel","0")
            self.set("reverse","False")
            self.set("calibrated","False")
            self.vals = cfg[self.sectionName]

        self.maxVal = cfg.getint(sectionName, 'top')
        self.minVal = cfg.getint(sectionName, 'bottom')
        self.mcp_pin = cfg.getint(sectionName, 'mcp_channel')
        self.reverse = cfg.getboolean(sectionName, 'reverse')
        self.calibrated = cfg.getboolean(sectionName, 'calibrated')
