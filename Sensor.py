import sys

import Config  # Our .ini file configuration class

# The clock "sensor" needs this
import datetime

# Here's our own module for reading the DHTxx Temp and Humidity Sensor
from dhtxx import DHTXX

# This is the Adafruit module that comes with CircuitPython
# It is used to read the (soil moisture and light) sensors attached to the MCP3xxx chip
# pip3 install adafruit-circuitpython-mcp3xxx
from adafruit_mcp3xxx.analog_in import AnalogIn # handles the sensor

class GenericSensor:
    def __getattr__(self, name):      # Check the config object's properties if
        retVal = self.cfg.get(name)   #   it's not on the sensor object itself
        return retVal

    def readObj(self):
        sensorResultDict = {
            "description": self.cfg.description,
            "sort": self.cfg.sort,
            "type": self.cfg.type,
            "field_name": self.cfg.field_name,
            "format": self.cfg.format,
            "reading": self.read()
        }
        return [sensorResultDict]

# ClockSensor: A "pretend" (software-only) sensor that returns the current time
class ClockSensor(GenericSensor):
    def __init__(self, iniSectionName):
        try:
            cfg = Config.ClockSensorConfig(iniSectionName)
            self.cfg = cfg

        except Exception as ex:
            # Handle other exceptions
            print(type(ex))
            print(ex.args)
            print(ex)
            raise(ex)

    def read_raw(self):
        return datetime.datetime.now()
    
    def read(self):
        return datetime.datetime.now().strftime(self.clock_format)

# DhtSensor: A digital sensor that returns the current temperature and humidity
class DhtSensor(GenericSensor):
    def __init__(self, iniSectionName):
        try:
            cfg = Config.DhtSensorConfig(iniSectionName)
            self.cfg = cfg
            self.temperature = None
            self.humidity = None
            self.error = None

            # set up DHTXX Sensor object
            self.sensor = DHTXX(pin=cfg.pin, sensorType=eval(cfg.dht_type), scale=eval(cfg.scale))
        except Exception as ex:
            # Handle other exceptions
            print(type(ex))
            print(ex.args)
            print(ex)
            raise(ex)

    def read_raw(self):
        return self.read()
    
    def read(self):
        dhtVal = self.sensor.read_and_retry()
        if dhtVal.is_valid():
            self.temperature = str(round(dhtVal.temperature,1))
            self.humidity = str(round(dhtVal.humidity,1))
            self.error = None
            return dhtVal
        else:
            print("Error: %d" % resdhtValult.error_code)
            self.temperature = None
            self.humidity = None
            self.error = dhtVal.error_code
            return {"Error": dhtVal.error_code}

    def readObj(self): # Need to override because we're returning two abjects
        dhtVal = self.read()
        if dhtVal.is_valid():
            sensorResultDict1 = {
                "description": self.cfg.description_temperature,
                "sort": int(self.cfg.sort_temperature),
                "type": self.cfg.type_temperature,
                "field_name": self.cfg.field_name_temperature,
                "format": self.cfg.format_temperature,
                "reading": self.temperature
            }
            sensorResultDict2 = {
                "description": self.cfg.description_humidity,
                "sort": int(self.cfg.sort_humidity),
                "type": self.cfg.type_humidity,
                "field_name": self.cfg.field_name_humidity,
                "format": self.cfg.format_humidity,
                "reading": self.humidity
            }
        return [sensorResultDict1,sensorResultDict2]


# McpSensor: An analog sensor that returns a scaled value between 0 and VALUE_RANGE_SIZE
# Used for Soil Moisture sensors and photo-resistor light sensors
# Connects to an MCP3xxx Analog-to-Digital converter chip
# Sensor must be calibrated to return a correct reading
VALUE_RANGE_SIZE = 100 # number of values in our converted moisture range
class McpSensor(GenericSensor):
    def __init__(self, iniSectionName, mcp):
        try:
            cfg = Config.McpSensorConfig(iniSectionName)
            self.cfg = cfg

            # set up MoistureSensor or Photoresistor object
            self.sensor = AnalogIn(mcp, cfg.mcp_pin)

            # Factor for converting readings to a 0-100 range
            self.factor = float(VALUE_RANGE_SIZE) / float(cfg.maxVal - cfg.minVal)

        except Exception as ex:
            # Handle other exceptions
            print(type(ex))
            print(ex.args)
            print(ex)
            raise(ex)

    # Returns raw value
    def read_raw(self):
        foundNewBounds = False
        val = self.sensor.value

        if (val > self.cfg.maxVal):         # Update the bounds in the ini file if it's outside
            foundNewBounds = True           # the range of values seen so far
            self.cfg.set('top', val)

        if (val < self.cfg.minVal):
            foundNewBounds = True
            self.cfg.set('bottom', val)
        
        if (foundNewBounds):
            # recalculate factor for converting readings to a 0-100 range
            self.factor = float(VALUE_RANGE_SIZE) / float(self.cfg.maxVal - self.cfg.minVal)

        return val
    
    # Reads value from sensor and returns value converted to range from 0 to VALUE_RANGE_SIZE
    def read(self):
        myVal = self.convert(self.read_raw())
        return str(round(myVal, 1))

    # converts raw values to something from 0 to VALUE_RANGE_SIZE
    def convert(self, val):
        newVal = float(val - self.cfg.minVal) * self.factor
        if self.cfg.reverse:
            newVal =  float(VALUE_RANGE_SIZE) - (newVal)
        
        return newVal
