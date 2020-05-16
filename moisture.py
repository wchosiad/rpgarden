import busio
import digitalio
import board
from time import sleep
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

CHIP_SELECT = board.D5 # This is the GPIO pin on the pi which comes from the MCP3008's CS/SHDN (pin 10) line
MCP_IN = MCP.P0    # this is the pin on the MCP3008 that the sensor's data line is attached to

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT)
mcp = MCP.MCP3008(spi, cs)

channel = AnalogIn(mcp, MCP_IN)


# for one sensor, the readings were in the range of 27904 (wet) to 56576 (dry)
lowVal = 27904
highVal = 56576
valueRange = 100
factor = (highVal - lowVal) / valueRange

minval = lowVal  # This will hold the smallest value we read
maxval = highVal # This will hold the biggest value we read

while True:
    rawVal = channel.value
    
    if (rawVal > maxval):
        maxval = rawVal
        highVal = rawVal
        factor = (highVal - lowVal) / valueRange

    if (rawVal < minval):
        minval = rawVal
        lowVal = rawVal
        factor = (highVal - lowVal) / valueRange

    val = (rawVal - lowVal) / factor
    print("Factored Val: ", val)

    print('Raw ADC Value: ', rawVal)
#    print('ADC Voltage: ' + str(channel.voltage) + 'V')
    print("Raw Min Value: ", minval, ', Raw Max Value: ', maxval) 
    print("============================================")
    sleep(1)
