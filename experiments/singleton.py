import configparser
import sys
from os import path
import traceback

class Single:
    RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"
    parserInstance = None # We want all updates to go through the class singleton variable, parserInstance

    def __init__(self, sectionName="General", cfgFile=RPGARDEN_CONFIG_FILE):
        # self.configFile = cfgFile              # Initialize instance members
        # self.sectionName = sectionName
        self.__dict__["configFile"] = cfgFile
        self.__dict__["sectionName"] = sectionName

        if not Single.parserInstance:                            # If parser hasn't already been initialized
            Single.parserInstance = configparser.ConfigParser()  # Create ConfigParser object

            if path.exists(cfgFile):                             # If the ini file exists
                Single.parserInstance.read(cfgFile)              # Load its data from the file
            else:
                Single.parserInstance.add_section(sectionName)   # It's a new ini file. Add the section and
                self.save()                                         # Write out the ini file

class SingleKid(Single):
    def __init__(self, sectionName="General", cfgFile=Single.RPGARDEN_CONFIG_FILE):
        super().__init__(sectionName, cfgFile)


foo = SingleKid()
print(foo.parserInstance.sections())

bar = SingleKid()
print(bar.parserInstance.sections())
