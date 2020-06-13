import configparser
from os import path

class RpgConfig:
    RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"

    def __init__(self, sectionName="General", cfgFile=RPGARDEN_CONFIG_FILE):
        self.rpgConfig = configparser.ConfigParser()  # Create ConfigParser object
        self.items = []                               # Initialize items list
        self.configFile = cfgFile
        self.sectionName = sectionName

        if path.exists(cfgFile):                      # Check to see if ini file exists
            self.rpgConfig.read(cfgFile)              # Load its data from the file
        else:
            self.rpgConfig.add_section(sectionName)   # New file. Add the section
            self.save()                               # Write out the ini file
        
        if sectionName in self.rpgConfig:
            self.items = self.rpgConfig.items(sectionName) # Load the section's info into the items list
        else:
            self.rpgConfig.add_section(sectionName)   # Existing file without section. Add the section
            self.save()                               # Write out the ini file
    
    def save(self):
        with open(self.configFile, 'w') as configfile:  # Write out the ini file
            self.rpgConfig.write(configfile)

    def set(self, key, value): 
        self.rpgConfig.set(self.sectionName, str(key), str(value))
        self.save()


class McpSensorConfig(RpgConfig):
    def __init__(self, sectionName, cfgFile=RpgConfig.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)

        cfg = self.rpgConfig

        if (len(self.items) == 0):
            self.set("top","35000")
            self.set("bottom","35001")
            self.set("mcp_channel","0")
            self.set("reverse","False")
            self.set("calibrated","False")
            self.items = cfg.items(self.sectionName)

        self.maxVal = cfg.getint(sectionName, 'top')
        self.minVal = cfg.getint(sectionName, 'bottom')
        self.mcp_pin = cfg.getint(sectionName, 'mcp_channel')
        self.reverse = cfg.getboolean(sectionName, 'reverse')
        self.calibrated = cfg.getboolean(sectionName, 'calibrated')


