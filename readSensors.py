import os
import sys, getopt  # Read command line arguments
import datetime
import Sensor
from Config import RpgConfig
import RPi.GPIO as GPIO

import csv        # Used for writing csv files
import socket     # Used to get host name
import traceback  # For error handling
import MySQLdb    # sudo apt-get update  - Do these commands to set up mysqldb in Python
                  # sudo apt-get upgrade
                  # sudo apt-get install python-dev default-libmysqlclient-dev
                  # pip3 install mysqlclient

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
import busio      # handles the SPI bus protocol
import digitalio  # handles IO on the GPIO pins
import board      # Raspberry Pi pin name constants, etc.
import adafruit_mcp3xxx.mcp3008 as MCP  # handles the MCP3008

# ==================================================================================================
# getUTCTime() - Gets current time in UTC as a string e.g.: 2020-08-21 20:20:20
# ==================================================================================================
def getUTCTime():
    clock_format = "%Y-%m-%d %H:%M:%S"
    return datetime.datetime.now(datetime.timezone( datetime.timedelta(hours=+0) )).strftime(clock_format)

# ==================================================================================================
# initialize() -Initialize pins and other stuff, Returns the mcp variable for handling the dtac
# ==================================================================================================
def initialize(rpgConfig):
    try:
        # That file contains the constants you can change to match your wiring
        if rpgConfig is None:
            rpgConfig = RpgConfig()

        # Set up the GPIO Pin Mode
        GPIO.setmode(GPIO.BCM)

        # MCP_3008 Chip Select Pin
        CHIP_SELECT_PIN = eval(rpgConfig.get("mcp_chip_select"))

        # Set up the SPI Bus, The chip select, and the MCP
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(CHIP_SELECT_PIN)
        mcp = MCP.MCP3008(spi, cs)
        return mcp
    except Exception as ex:
        # Handle other exceptions
        print(traceback.format_exc())
        print(type(ex))
        print(ex.args)
        print(ex)

# ==================================================================================================
# getSensorList() - Creates a list of sensors and their properties based on info in a config file
# ==================================================================================================
def getSensorList(rpgConfig, mcp):
    try:
        print("Getting Sensor Info...")

        # Returns a list of sensors
        mySensors = []

        # Read sensor info from the .ini file
        # That file contains the constants you can change to match your wiring
        if rpgConfig is None:
            rpgConfig = RpgConfig()

        # Set up the sensors. Store them in the mySensors list
        sensorList = rpgConfig.get("sensor_list" + "_" + socket.gethostname()).split(',')
        for sensorSection in sensorList:
            sensorName = sensorSection + "_" + socket.gethostname()
            sensortype = rpgConfig.getSensorType(sensorName)

            if sensortype == "dht":
                mySensors.append(Sensor.DhtSensor(sensorName))

            if sensortype == "photo" or sensortype == "moisture":
                mySensors.append(Sensor.McpSensor(sensorName, mcp))
        return mySensors
    except Exception as ex:
        # Handle other exceptions
        print(traceback.format_exc())
        print(type(ex))
        print(ex.args)
        print(ex)


# ==================================================================================================
# getReadings() - Given a list of Sensors, returns a list of sensor readings
# ==================================================================================================
def getReadings(sensors):
    try:
        # Collect the data from each sensor
        # A "reading" object has properties for:
        #    description, sort, type, field_name, format, and reading
        print("Collecting data...")
        myReadings = []
        for sensor in sensors:
            myReadings.extend(sensor.readObj())

        # Sort readings
        myReadings.sort(key=lambda x: x["sort"], reverse=False)  
        print("Data collected and sorted.")

        return myReadings
    except Exception as ex:
        # Handle other exceptions
        print(traceback.format_exc())
        print(type(ex))
        print(ex.args)
        print(ex)





# ==================================================================================================
# writeCSV() - Save the data to a tab-delimited file
# ==================================================================================================
def writeCSV(rpgConfig, readings):
    try:
        # Read sensor info from the .ini file
        # That file contains the constants you can change to match your wiring
        if rpgConfig is None:
            rpgConfig = RpgConfig()

        # Log directory and file path
        RPGARDEN_LOG_DIR = rpgConfig.get("log_dir")
        RPGARDEN_LOG_FILE = rpgConfig.get("log_file")

        print("Saving Data to file.")
        # Check if the path to the log file exists, if not, create it
        if not os.path.exists(RPGARDEN_LOG_DIR):
            os.makedirs(RPGARDEN_LOG_DIR)

        # Check if the log file exists, if not, initialize it with a header row
        if not os.path.exists(RPGARDEN_LOG_FILE):
            fieldNames = []
            fieldNames.append("Time")
            for reading in readings:
                fieldNames.append(reading.field_name)
            
            with open(RPGARDEN_LOG_FILE, mode='w') as logFile:
                logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
                logFile_writer.writerow(fieldNames)

        # write out the values
        fieldVals = []
        fieldVals.append(getUTCTime())
        for reading in readings:
            fieldVals.append(reading["reading"])

        with open(RPGARDEN_LOG_FILE, mode='a') as logFile:
            logFile_writer = csv.writer(logFile, dialect=csv.excel_tab, quoting=csv.QUOTE_NONE)
            logFile_writer.writerow(fieldVals)
    except Exception as ex:
        # Handle other exceptions
        print(traceback.format_exc())
        print(type(ex))
        print(ex.args)
        print(ex)


# ==================================================================================================
# writeSQL() - Save the data to a MySQL/MariaDB database
# ==================================================================================================
def writeSQL(rpgConfig, readings):
    try:
        # Read sensor info from the .ini file
        # That file contains the constants you can change to match your wiring
        if rpgConfig is None:
            rpgConfig = RpgConfig()

        print("Saving data to database...")
        # Open database connection
        db = MySQLdb.connect(rpgConfig.private['mysql_host'], rpgConfig.private['mysql_user'], rpgConfig.private['mysql_password'], rpgConfig.private['mysql_db'])
        cursor = db.cursor()
        sql = "INSERT INTO rpgarden2 (pk, host, reading_time, sensor_name, sensor_type, sensor_value) VALUES (NULL,  %s, %s, %s, %s, %s)"

        strCurrentTime = getUTCTime()
        print("UTC time: " + strCurrentTime)
        try:
            for reading in readings:
                fieldVals = (socket.gethostname(), strCurrentTime, reading["field_name"], reading["type"], reading["reading"])
                cursor.execute(sql, fieldVals)
                print("Writing " + reading["description"] + " value to database")

            db.commit()
            print("New readings committed in database.")
        except:
            print(traceback.format_exc())
            print("!!! Failed to save MySQL data! Sensor: " + sensor.field_name)
            db.rollback()

        # disconnect from server
        db.close()
    except Exception as ex:
        # Handle other exceptions
        print(traceback.format_exc())
        print(type(ex))
        print(ex.args)
        print(ex)



# ==================================================================================================
# Code for reading and logging the data
# ==================================================================================================
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc", ["help", "configure"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print("Unknown option provided")
        print("usage: python3 readSensors.py [-c <sensorname>]")
        print("   where: <sensorname> is an optional sensor to be configured")
        sys.exit(2)

    try:
        myRpgConfig = RpgConfig()

        if len(sys.argv) > 1:
            for o, a in opts:
                if o in ("-c", "configure"):
                    pass # ToDo: Add calibration code
                elif o in ("-h", "--help"):
                    print("usage: python3 readSensors.py [-c <sensorname>]")
                    print("   where: <sensorname> is an optional sensor to be configured")
                    sys.exit()
                else:
                    print("Unknown option")
                    print("usage: python3 readSensors.py [-c <sensorname>]")
                    print("   where: <sensorname> is an optional sensor to be configured")
                    sys.exit()
        else:
            myMCP = initialize(myRpgConfig)
            mySensors = getSensorList(myRpgConfig, myMCP)
            myReadings = getReadings(mySensors)
            # Write data to tab-delimited CSV
            writeCSV(myRpgConfig, myReadings)
            # Write data to MySQL/MariaDB Database
            writeSQL(myRpgConfig, myReadings)
    except KeyboardInterrupt:    
        pass  # Don't do anything special if user typed Ctrl-C

    except Exception as ex:
        # Handle other exceptions
        print(traceback.format_exc())
        print(type(ex))
        print(ex.args)
        print(ex)

if __name__ == "__main__":
   main()