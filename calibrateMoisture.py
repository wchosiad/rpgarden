from time import sleep
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
RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden/rpgarden.ini"

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)

# Set up the moisture sensor
moistureSensor = AnalogIn(mcp, MOISTURE_MCP_PIN)

# Our starting readings (defaults)
minVal = 35000
maxVal = 35000

# get thresholds from config file
rpgConfig = configparser.ConfigParser() # Create ConfigParser object
rpgConfig.read(RPGARDEN_CONFIG_FILE)    # Load its data from the file
if 'moisture_sensor_thresholds' in rpgConfig:
    # Create an object to hold a section of the ini file
    moistureSection = rpgConfig['moisture_sensor_thresholds']

    # Set variables from the configparser. Changes to the section
    # are stored in the ConfigParser object, rpgConfig
    minVal = int(moistureSection['bottom'])
    maxVal = int(moistureSection['top'])

print("============================================")

# Loop, checking to see if the value read is outside of 
# the existing thresholds
try:
    while True:
        val = moistureSensor.value
        print("Reading: ", val)
        if (val < minVal):
            minVal = val
            print('***** New Minimum Value: ', minVal)

            # Update the ini file
            moistureSection['bottom'] = str(minVal)
            with open(RPGARDEN_CONFIG_FILE, 'w') as configfile:
                rpgConfig.write(configfile)

        if (val > maxVal):
            maxVal = val
            print('***** New Maximum Value: ', maxVal)

            # Update the ini file
            moistureSection['top'] = str(maxVal)
            with open(RPGARDEN_CONFIG_FILE, 'w') as configfile:
                rpgConfig.write(configfile)

        print("========================= ", minVal, " - ", maxVal)
        sleep(1)
except Exception as ex:
    print(type(ex))
    print(ex.args)
    print(ex)
finally:
    print("Range: ", minVal, " - ", maxVal)
