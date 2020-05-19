# File: calibrateMoisture.py
# --------------------------
# Run this program for a while while moving the moisture sensor 
# in and out of the water.
from time import sleep
from os import path
import configparser

# These are all Adafruit modules that come with CircuitPython
import busio      # handles the SPI bus protocol
import digitalio  # handles IO on the GPIO pins
import board      # Raspberry Pi pin name constants, etc.
import adafruit_mcp3xxx.mcp3008 as MCP         # handles the MCP3008
from adafruit_mcp3xxx.analog_in import AnalogIn # handles the sensor

# Here are the  constants you can change to match your wiring
# This is the GPIO pin that connects to the MCP's CS/SHDN (pin 10)
CHIP_SELECT_PIN = board.D5

# This is the pin on the MCP that's connected to the moisture sensor
MOISTURE_MCP_PIN = MCP.P0

# This is the path to the configuration file
RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)

# Set up the moisture sensor
moistureSensor = AnalogIn(mcp, MOISTURE_MCP_PIN)

# Our starting readings (defaults)
maxVal = 35000
minVal = 35000

# get thresholds from config file
rpgConfig = configparser.ConfigParser()  # Create ConfigParser
if path.exists(RPGARDEN_CONFIG_FILE):    # if ini file exists...
    rpgConfig.read(RPGARDEN_CONFIG_FILE) # Load data from the file
    # Note: if ini file doesn't exist, this does not throw an error

if 'moisture_sensor_1' in rpgConfig:
    # Create a section object to hold part of the ini file
    moistureSection = rpgConfig['moisture_sensor_1']

    # Set variables from the configparser.
    # Note that all ini file values are treated as strings, so they 
    # need to be converted when reading or saving
    maxVal = int(moistureSection['top'])
    minVal = int(moistureSection['bottom'])
else:
    # add the moisture_sensor_1 section if it doesn't exist
    # and save the ini file
    rpgConfig.add_section("moisture_sensor_1")
    moistureSection = rpgConfig['moisture_sensor_1']
    moistureSection["top"] = str(maxVal)
    moistureSection["bottom"] = str(minVal)
    with open(RPGARDEN_CONFIG_FILE, 'w') as configfile:
        rpgConfig.write(configfile)

# Loop, checking to see if the value read is outside of 
# the existing thresholds
try:
    while True:
        foundNewVal = False
        val = moistureSensor.value

        if (val > maxVal):
            foundNewVal = True
            maxVal = val
            moistureSection['top'] = str(maxVal)
            print('***** New Maximum Value: ', maxVal)

        if (val < minVal):
            foundNewVal = True
            minVal = val
            moistureSection['bottom'] = str(minVal)
            print('***** New Minimum Value: ', minVal)

        if (foundNewVal):  # Update the ini file
            with open(RPGARDEN_CONFIG_FILE, 'w') as configfile:
                rpgConfig.write(configfile)

        print("Reading:", val, " Sensor Range:", minVal, "-", maxVal)
        sleep(1)

except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(type(ex))
    print(ex.args)
    print(ex)

finally:
    print("\nFinal Range: ", minVal, " - ", maxVal)
