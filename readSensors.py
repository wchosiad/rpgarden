import os
import Sensor
from Config import RpgConfig
import RPi.GPIO as GPIO
import csv
import socket     # Used to get host name

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
import busio      # handles the SPI bus protocol
import digitalio  # handles IO on the GPIO pins
import board      # Raspberry Pi pin name constants, etc.
import adafruit_mcp3xxx.mcp3008 as MCP  # handles the MCP3008

try:
    # Read sensor info from the .ini file
    # That file contains the constants you can change to match your wiring
    rpgConfig = RpgConfig()

    # Set up the GPIO Pin Mode
    GPIO.setmode(GPIO.BCM)

    # MCP_3008 Chip Select Pin
    CHIP_SELECT_PIN = eval(rpgConfig.get("mcp_chip_select"))

    # Set up the SPI Bus, The chip select, and the MCP
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
    mcp = MCP.MCP3008(spi, cs)

    # Log directory and file path
    RPGARDEN_LOG_DIR = rpgConfig.get("log_dir")
    RPGARDEN_LOG_FILE = rpgConfig.get("log_file")

    # Set up the sensors. Store them in the sensors list
    sensors = []
    sensorList = rpgConfig.get("sensor_list").split(',')
    for sensorSection in sensorList:
        sensorName = sensorSection + "_" + socket.gethostname()
        sensortype = rpgConfig.getSensorType(sensorName)

        if sensortype == "clock":
            sensors.append(Sensor.ClockSensor(sensorName))

        if sensortype == "dht":
            sensors.append(Sensor.DhtSensor(sensorName))

        if sensortype == "photo" or sensortype == "moisture":
            sensors.append(Sensor.McpSensor(sensorName, mcp))

    sensors.sort(key=lambda x: x.cfg.sort, reverse=False)  # Sort sensors by sort order from config file

    # Check if the path to the log file exists, if not, create it
    if not os.path.exists(RPGARDEN_LOG_DIR):
        os.makedirs(RPGARDEN_LOG_DIR)

    # Check if the log file exists, if not, initialize it with a header row
    if not os.path.exists(RPGARDEN_LOG_FILE):
        fieldnames = []
        for sensor in sensors:
            fieldnames.extend(sensor.cfg.field_name.split("~"))
        
        with open(RPGARDEN_LOG_FILE, mode='w') as logFile:
            logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
            logFile_writer.writerow(fieldnames)

    fieldVals = []
    for sensor in sensors:
        val = sensor.read()
        if (sensor.cfg.type != 'dht'):
            print(sensor.cfg.description + ": " + val)
            fieldVals.append(val)
        else:
            print("Temperature: " + sensor.temperature)
            print("Humidity: " + sensor.humidity)
            fieldVals.append(sensor.temperature)
            fieldVals.append(sensor.humidity)

    with open(RPGARDEN_LOG_FILE, mode='a') as logFile:
        logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
        logFile_writer.writerow(fieldVals)
    
except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(type(ex))
    print(ex.args)
    print(ex)
