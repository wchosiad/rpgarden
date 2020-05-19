import RPi.GPIO as GPIO
from dhtxx import DHTXX
from time import sleep

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# read data using GPIO #16 pin for a DHT22 sensor with results in FAHRENHEIT
instance = DHTXX(pin=16, sensorType=DHTXX.DHT22, scale=DHTXX.FAHRENHEIT)

print("Reading Sensor...")
result = instance.read_and_retry()
if result.is_valid():
    print("Temperature: %-3.1f F" % result.temperature)
    print("Humidity: %-3.1f %%" % result.humidity)
else:
    print("Error: %d" % result.error_code)

GPIO.cleanup()
