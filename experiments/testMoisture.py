from time import sleep

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

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)

# Set up the moisture sensor
moistureSensor = AnalogIn(mcp, MOISTURE_MCP_PIN)

print("============================================")
for i in range(3):
    print('Raw ADC Value: ', moistureSensor.value)
    print('ADC Voltage: ', str(moistureSensor.voltage) + 'V')
    print("============================================")
    sleep(1)
