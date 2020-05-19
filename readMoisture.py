from time import sleep
from McpSensor import McpSensor 

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
import busio      # handles the SPI bus protocol
import digitalio  # handles IO on the GPIO pins
import board      # Raspberry Pi pin name constants, etc.
import adafruit_mcp3xxx.mcp3008 as MCP  # handles the MCP3008

# Here are the constants you can change to match your wiring
CHIP_SELECT_PIN = board.D5 #GPIO Pin for MCP's Chip Select

# This is the path to the configuration file
RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)

sensor = McpSensor(mcp, RPGARDEN_CONFIG_FILE, "moisture_sensor_1")

try:
    while True:
        val = sensor.read_raw()
        print(val, "    %.2f" % sensor.convert(val))
        sleep(1)
except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(type(ex))
    print(ex.args)
    print(ex)
