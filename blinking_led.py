import RPi.GPIO as GPIO    # Import Raspberry Pi GPIO library
from time import sleep     # Import the sleep function from the time module

GPIO.setwarnings(False)    # Ignore warning for now
GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering
GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)   # Set pin 8 to be an output pin and set initial value to low (off)

for i in range(5):
    print('Turning on')
    GPIO.output(8, GPIO.HIGH)   # Turn on
    sleep(.25)                  # Sleep for a short while
    print('Turning off')
    GPIO.output(8, GPIO.LOW)    # Turn off
    sleep(.25)                  # Sleep again

GPIO.cleanup()
