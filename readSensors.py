from time import sleep
import os
import configparser
from McpSensor import McpSensor 
import RPi.GPIO as GPIO
from dhtxx import DHTXX
import csv
import datetime
import socket

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
import busio      # handles the SPI bus protocol
import digitalio  # handles IO on the GPIO pins
import board      # Raspberry Pi pin name constants, etc.
import adafruit_mcp3xxx.mcp3008 as MCP  # handles the MCP3008

# Here are the constants you can change to match your wiring
CHIP_SELECT_PIN = board.D6     # It may be that board.D5 is blown on my Pi - it doesn't seem to work with this any more

#Config and Log files
RPGARDEN_LOG_DIR = "/home/pi/code/rpgarden/logs"
RPGARDEN_LOG_FILE = RPGARDEN_LOG_DIR + "/datalog.csv"
print("Log FIle: " + RPGARDEN_LOG_FILE)

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)
moistureSensor = McpSensor(mcp, "moisture_sensor_1_" + socket.gethostname())
photoSensor = McpSensor(mcp, "photo_sensor_1_" + socket.gethostname())

# Set up for the DHT sensor
GPIO.setmode(GPIO.BCM)
dhtSensor = DHTXX(pin=16, sensorType=DHTXX.DHT22, scale=DHTXX.FAHRENHEIT)

if not os.path.exists(RPGARDEN_LOG_DIR):
    os.makedirs(RPGARDEN_LOG_DIR)

# Check if the log file exists, if not, initialize it with a header row
if not os.path.exists(RPGARDEN_LOG_FILE):
    with open(RPGARDEN_LOG_FILE, mode='w') as logFile:
        fieldnames = ['log_date', 'temperature', 'humidity','soil_moisture','light']
        logFile_writer = csv.writer(logFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        logFile_writer.writerow(fieldnames)

# just read the sensors once and log it.
try:
    moistureVal = moistureSensor.read()
    print( "Soil Moisture: %.2f" % moistureVal)

    photoVal = photoSensor.read()
    print( "Light Sensor: %.2f" % photoVal)

    dhtVal = dhtSensor.read_and_retry()
    if dhtVal.is_valid():
        print("Temperature: %-3.1f F" % dhtVal.temperature)
        print("Humidity: %-3.1f %%" % dhtVal.humidity)
    else:
        print("Error: %d" % resdhtValult.error_code)

    with open(RPGARDEN_LOG_FILE, mode='a') as logFile:
        fieldnames = ['log_date', 'temperature', 'humidity','soil_moisture','light']
        logFile_writer = csv.writer(logFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        logFile_writer.writerow([datetime.datetime.now(), dhtVal.temperature, dhtVal.humidity, moistureVal, photoVal])
    
    print("\n")

except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(type(ex))
    print(ex.args)
    print(ex)
