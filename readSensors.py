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

    sensors.sort(key=lambda x: x.cfg.sort, reverse=False)  # Sort sensors by sort order from config file


    # ==================================================================================================
    # Code for saving the data to a tab-delimited file
    # ==================================================================================================
    
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

    # Collect the data
    fieldVals = []
    fieldNames = []
    fieldFormats = []
    strCurrentTime = None
    for sensor in sensors:
        val = sensor.read()
        if (sensor.type != 'dht'):
            print(sensor.description + ": " + val)
            fieldVals.append(val)
            fieldNames.append(sensor.field_name)
            fieldFormats.append(sensor.format)
            if sensor.type == 'clock':
                strCurrentTime = val
        else:
            print("Temperature: " + sensor.temperature)
            fieldVals.append(sensor.temperature)
            fieldNames.append("temperature")
            fieldFormats.append("%s")

            print("Humidity: " + sensor.humidity)
            fieldVals.append(sensor.humidity)
            fieldNames.append("humidity")
            fieldFormats.append("%s")

    with open(RPGARDEN_LOG_FILE, mode='a') as logFile:
        logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
        logFile_writer.writerow(fieldVals)


    # ==================================================================================================
    # Code for saving the data to a remote MySQL database (wide table)
    # ==================================================================================================
    print("\nCollecting data to save to MySQL...")
    fieldNames.append("pk")
    fieldVals.append(None)
    fieldFormats.append("%s")
    
    fieldNames.append("host")
    fieldVals.append(socket.gethostname())
    fieldFormats.append("%s")

    strFieldNames = ','.join(fieldNames) 
    strFieldFormats = ','.join(fieldFormats) 
    sql = "INSERT INTO rpgarden (" + strFieldNames + ") VALUES (" +  strFieldFormats + ")"

    print("Saving data to MySQL (wide)...")
    # Open database connection
    db = MySQLdb.connect(rpgConfig.private['mysql_host'], rpgConfig.private['mysql_user'], rpgConfig.private['mysql_password'], rpgConfig.private['mysql_db'])
    cursor = db.cursor()
    
    try:
        # Execute the SQL command
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

    for sensor in sensors:
        val = sensor.read()
        if (sensor.type == 'dht'):
            try:
                fieldVals = (socket.gethostname(), strCurrentTime, "temperature", sensor.temperature)
                cursor.execute(sql, fieldVals)
                db.commit()
                print("Data Saved for temperature")

                fieldVals = (socket.gethostname(), strCurrentTime, "humidity", sensor.humidity)
                cursor.execute(sql, fieldVals)
                db.commit()
                print("Data Saved for humidity")
            except:
                # Rollback in case there is any error
                print(traceback.format_exc())
                print("!!! Failed to save MySQL data! Sensor: " + sensor.field_name)
                db.rollback()
        elif sensor.type != 'clock':
            try:
                fieldVals = (socket.gethostname(), strCurrentTime, sensor.field_name, val)
                # Execute the SQL command
                cursor.execute(sql, fieldVals)
                # Commit your changes in the database
                db.commit()
                print("Data Saved for " + sensor.field_name)
            except:
                # Rollback in case there is any error
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
