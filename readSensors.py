import os
import Sensor
from Config import RpgConfig
import RPi.GPIO as GPIO
import csv
import socket     # Used to get host name
import traceback
import MySQLdb    # pip3 install mysqlclient
                  # sudo apt-get install python-dev default-libmysqlclient-dev
                  #

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
    sensorList = rpgConfig.get("sensor_list" + "_" + socket.gethostname()).split(',')
    for sensorSection in sensorList:
        sensorName = sensorSection + "_" + socket.gethostname()
        sensortype = rpgConfig.getSensorType(sensorName)

        if sensortype == "clock":
            sensors.append(Sensor.ClockSensor(sensorName))

        if sensortype == "dht":
            sensors.append(Sensor.DhtSensor(sensorName))

        if sensortype == "photo" or sensortype == "moisture":
            sensors.append(Sensor.McpSensor(sensorName, mcp))

    # ==================================================================================================
    # Code for reading and logging the data
    # ==================================================================================================

    # Collect the data
    print("\Collecting data...")
    readings = []
    readingsWithClock = []
    clockReading = None # The clock sensor is special because everyone uses it
    for sensor in sensors:
        if sensor.type == 'clock':
            clockReading = (sensor.readObj())[0]
            readingsWithClock.extend([clockReading])
        else:
            readings.extend(sensor.readObj())
            readingsWithClock.extend(sensor.readObj())

    # Sort readings
    readings.sort(key=lambda x: x["sort"], reverse=False)  
    readingsWithClock.sort(key=lambda x: x["sort"], reverse=False)  
    print("\Data collected.")

    # ==================================================================================================
    # Code for saving the data to a tab-delimited file
    # ==================================================================================================
    print("\Saving Data to file.")
    # Check if the path to the log file exists, if not, create it
    if not os.path.exists(RPGARDEN_LOG_DIR):
        os.makedirs(RPGARDEN_LOG_DIR)

    # Check if the log file exists, if not, initialize it with a header row
    if not os.path.exists(RPGARDEN_LOG_FILE):
        fieldNames = []
        for reading in readingsWithClock:
            fieldNames.append(reading.field_name)
        
        with open(RPGARDEN_LOG_FILE, mode='w') as logFile:
            logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
            logFile_writer.writerow(fieldNames)

    # write out the values
    fieldVals = []
    for reading in readingsWithClock:
        fieldVals.append(reading["reading"])

    with open(RPGARDEN_LOG_FILE, mode='a') as logFile:
        logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
        logFile_writer.writerow(fieldVals)


    # ==================================================================================================
    # Code for saving the data to a remote MySQL database (wide table)
    # ==================================================================================================
    print("\Formatting data to save to MySQL...")
    fieldNames = []
    fieldVals = []
    fieldFormats = []

    fieldNames.append("pk")
    fieldVals.append(None)
    fieldFormats.append("%s")
    
    fieldNames.append("host")
    fieldVals.append(socket.gethostname())
    fieldFormats.append("%s")

    fieldNames.append(clockReading["field_name"])
    fieldVals.append(clockReading["reading"])
    fieldFormats.append(clockReading["format"])

    for reading in readings:
        fieldNames.append(reading["field_name"])
        fieldVals.append(reading["reading"])
        fieldFormats.append(reading["format"])

    strFieldNames = ','.join(fieldNames) 
    strFieldFormats = ','.join(fieldFormats) 
    sql = "INSERT INTO rpgarden (" + strFieldNames + ") VALUES (" +  strFieldFormats + ")"

    print("Saving data to MySQL (wide)...")
    # Open database connection
    db = MySQLdb.connect(rpgConfig.private['mysql_host'], rpgConfig.private['mysql_user'], rpgConfig.private['mysql_password'], rpgConfig.private['mysql_db'])
    cursor = db.cursor()
    
    try:
        # Execute the SQL command
        #cursor.execute("SET time_zone = '" + rpgConfig.private['mysql_timezone'] + "';")
        cursor.execute(sql, fieldVals)
        # Commit your changes in the database
        db.commit()
        print("Data Saved")
    except:
        # Rollback in case there is any error
        print(traceback.format_exc())
        print("!!! Failed to save MySQL data!")
        db.rollback()

    # disconnect from server
    db.close()


    # ==================================================================================================
    # Code for saving the data to a remote MySQL database (narrow table)
    # ==================================================================================================
    print("Saving data to MySQL (narrow)...")
    # Open database connection
    db = MySQLdb.connect(rpgConfig.private['mysql_host'], rpgConfig.private['mysql_user'], rpgConfig.private['mysql_password'], rpgConfig.private['mysql_db'])
    cursor = db.cursor()
    sql = "INSERT INTO rpgarden2 (pk, host, reading_time, sensor_name, sensor_value) VALUES (NULL,  %s, %s, %s, %s)"

    strCurrentTime = clockReading["reading"]

    try:
        for reading in readings:
            fieldVals = (socket.gethostname(), strCurrentTime, reading["field_name"], reading["reading"])
            cursor.execute(sql, fieldVals)
            print("Data Saved for " + reading["description"])

        db.commit()
    except:
        print(traceback.format_exc())
        print("!!! Failed to save MySQL data! Sensor: " + sensor.field_name)
        db.rollback()

    # disconnect from server
    db.close()

except KeyboardInterrupt:    
    pass  # Don't do anything special if user typed Ctrl-C

except Exception as ex:
    # Handle other exceptions
    print(traceback.format_exc())
    print(type(ex))
    print(ex.args)
    print(ex)
