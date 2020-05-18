from MoistureSensor import MoistureSensor 
from time import sleep

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
import busio      # handles the SPI bus protocol
import digitalio  # handles IO on the GPIO pins
import board      # Raspberry Pi pin name constants, etc.
import adafruit_mcp3xxx.mcp3008 as MCP  # handles the MCP3008

# Here are the constants you can change to match your wiring
CHIP_SELECT_PIN = board.D5 #GPIO Pin for MCP's Chip Select
MOISTURE_MCP_PIN = MCP.P0  #MCP sensor input pin

# This is the path to the configuration file
RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)

sensor = MoistureSensor(mcp, MOISTURE_MCP_PIN, RPGARDEN_CONFIG_FILE, "moisture_sensor_2")

try:
    while True:
        print(sensor.read_raw(), "    %.2f" % sensor.read())
        sleep(1)
except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(type(ex))
    print(ex.args)
    print(ex)
