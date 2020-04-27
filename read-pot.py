import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import time

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI) # create the spi bus
cs = digitalio.DigitalInOut(board.D5) # create the cs (chip select)
mcp = MCP.MCP3008(spi, cs) # create the mcp object

# Analog-ti-Digital Channel Pins on the mcp3008
chan_pot = AnalogIn(mcp, MCP.P0) # pin 0 for the potentiometer
chan_pr = AnalogIn(mcp, MCP.P1)  # pin 1 for the photoresistor
chan_ms = AnalogIn(mcp, MCP.P2)  # pin 2 for the Moisture Sensor

# Calibration Constants
MS_MIN = 28614  # Moisture Sensor Minimum (in water)
MS_MAX = 56237  # Moisture Sensor Maximum (dry in air)

def read_channel_value(channel) :
        sampleSize = 50
        cum = 0
        for j in range(sampleSize):
                reading = channel.value
                #print(reading)
                cum = cum + reading
                #time.sleep(.01)
        rawVal = int(round(cum/sampleSize,0))
        return rawVal

def read_channel_voltage(channel) :
        sampleSize = 50
        cum = 0
        for j in range(sampleSize):
                reading = channel.voltage
                #print(reading)
                cum = cum + reading
                time.sleep(.01)
        rawVal = cum/sampleSize
        return rawVal

def convertToPct(reading, expectedMinVal, expectedMaxVal, precision = 0):
        factor = 100 / (expectedMaxVal - expectedMinVal)
        pct = round((val-expectedMinVal)*factor, precision)
        if pct < 0:
                pct = 0.0
        if pct > 100:
                pct = 100.0
        if precision == 0:
                pct = int(pct)
        return pct


for i in range(10) :
        val = read_channel_value(chan_ms)
        if i == 0:
                maxval = minval = val
        pct = convertToPct(val, MS_MIN, MS_MAX, 2)
        print('Raw Pot ADC Value: ' + str(val) + ', %: ' + str(pct) )
        if val > maxval :
                maxval = val
        if val < minval :
                minval = val
if (minval < MS_MIN or maxval > MS_MAX):
        print("Expected bounds (" + str(MS_MIN) + "-" + str(MS_MAX) + ") exceeded - minval: " + str(minval) + ", maxval: " + str(maxval))





# sampleSize = 50
# i = 20
# while i > 0 :
#         # print('Raw Pot ADC Value: ', chan_pot.value)
#         # print('Pot ADC Voltage: ' + str(chan_pot.voltage) + 'V')
#         # print('Raw PR ADC Value: ', chan_pr.value)
#         # print('PR ADC Voltage: ' + str(chan_pr.voltage) + 'V')
#         # print(("*" * int(chan_pr.voltage * 10)) + " " + str(chan_pr.value)  )

#         cum = 0
#         for j in range(sampleSize):
#                 reading = chan_pr.value
#                 #print(reading)
#                 cum = cum + reading
#                 time.sleep(.01)
#         rawVal = cum/sampleSize
#         roundVal = round((rawVal/1000),0)
#         val = int(round((roundVal - 3) * (10/6),0))
# #        val = (int(round(rawVal/1000,0)) - 13) * 2
#         #print(("*" * int(chan_pr.value/1000)) + " " + str(chan_pr.value)  + " " + str(val)  )
#         print(("*" * val) + " " + str(val) + " " + str(roundVal) )
#         i = i - 1
#         #time.sleep(1)
