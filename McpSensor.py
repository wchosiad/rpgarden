from os import path
import configparser
from SensorConfig import McpSensorConfig

# These are all Adafruit modules that come with CircuitPython
# pip3 install adafruit-circuitpython-mcp3xxx
from adafruit_mcp3xxx.analog_in import AnalogIn # handles the sensor

VALUE_RANGE_SIZE = 100 # number of values in our converted moisture range

class McpSensor:
    def __init__(self, mcp, iniSectionName):
        try:
            cfg = McpSensorConfig(iniSectionName)
            self.cfg = cfg

            # set up MoistureSensor object
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
            foundNewBounds = True           # of the values seen so far
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
        return self.convert(self.read_raw())

    # converts raw values to something from 0 to VALUE_RANGE_SIZE
    def convert(self, val):
        newVal = float(val - self.cfg.minVal) * self.factor
        if self.cfg.reverse:
            newVal =  float(VALUE_RANGE_SIZE) - (newVal)
        
        return newVal
