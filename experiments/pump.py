import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)

GPIO.setup(4, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)


GPIO.output(17, False)
GPIO.output(27, True)

# GPIO.output(4, True)
# sleep(10)

pwm=GPIO.PWM(4, 100)
pwm.start(0)
pwm.ChangeDutyCycle(100)
GPIO.output(4, True)

sleep(2.5)
pwm.ChangeDutyCycle(40)
sleep(3)

GPIO.output(4, False)
GPIO.cleanup()