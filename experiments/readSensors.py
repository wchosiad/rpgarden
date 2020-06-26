from time import sleep
from os import path
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
CHIP_SELECT_PIN = board.D5 #GPIO Pin for MCP's Chip Select

#Config and Log files
RPGARDEN_CONFIG_FILE = "/home/pi/code/rpgarden/rpgarden.ini"
RPGARDEN_LOG_FILE = "/home/pi/code/rpgarden/logs/datalogTest.csv"

# Set up the SPI Bus, The chip select, and the MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
mcp = MCP.MCP3008(spi, cs)
moistureSensor = McpSensor(mcp, RPGARDEN_CONFIG_FILE, \
                           "moisture_sensor_1_" + socket.gethostname())
photoSensor = McpSensor(mcp, RPGARDEN_CONFIG_FILE, \
                        "photo_sensor_1_" + socket.gethostname())

# Set up for the DHT sensor
GPIO.setmode(GPIO.BCM)
dhtSensor = DHTXX(pin=16, sensorType=DHTXX.DHT22, \
                  scale=DHTXX.FAHRENHEIT)

# Check if the log file exists, if not, start with a header row
if not path.exists(RPGARDEN_LOG_FILE):
    with open(RPGARDEN_LOG_FILE, mode='w') as logFile:
        fieldnames = ['log_date', 'temperature', 'humidity',\
                      'soil_moisture','light']
        logFile_writer = csv.writer(logFile)
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
        logFile_writer = csv.writer(logFile)
        logFile_writer.writerow([datetime.datetime.now(), \
                                 round(dhtVal.temperature,2), \
                                 round(dhtVal.humidity,2),\
                                 round(moistureVal,2), \
                                 round(photoVal,2)])
    
    print("\n")

except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(type(ex))
    print(ex.args)
    print(ex)
