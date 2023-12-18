# https://simonprickett.dev/using-a-break-beam-sensor-with-python-and-raspberry-pi/
# https://learn.adafruit.com/photocells/circuitpython
# https://raspi.tv/2013/rpi-gpio-basics-6-using-inputs-and-outputs-together-with-rpi-gpio-pull-ups-and-pull-downs

from enum import Enum
import RPi.GPIO as GPIO
import time

class SensorLocation(Enum):
    BeforeTollBar = 0
    UnderTollBar = 1
    BehindTollBar = 2

class Sensor():
    def __init__(self, portGPIO, location) -> None:
        self.port = portGPIO
        self.location = location
        self.value = False

class BarrierState(Enum):
    Closed = 0
    Open = 1

class Barrier():
    def __init__(self, portGPIO) -> None:
        self.port = portGPIO
        self.state = BarrierState.Closed

class TollBarManager:
    def __init__(self, sensorBeforeTollBarPort=17, sensorUnderTollBarPort=18, sensorBehindTollBarPort=19, barrierPort=20) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(sensorBeforeTollBarPort, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(sensorUnderTollBarPort, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(sensorBehindTollBarPort, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(barrierPort, GPIO.OUT)
        self.sensors = [Sensor(sensorBeforeTollBarPort, SensorLocation.BeforeTollBar),
                        Sensor(sensorUnderTollBarPort, SensorLocation.UnderTollBar),
                        Sensor(sensorBehindTollBarPort, SensorLocation.BehindTollBar)]
        self.barrier = Barrier(barrierPort)
        self.openGateTime = 7 # time in sec
        self.startTimerForBarrier = 0
        self.endTimer = 0

    def __del__(self):
        GPIO.cleanup()
    
    def getSensorByLocation(self, location):
        if location == SensorLocation.BeforeTollBar:
            return self.sensors[0]
        elif location == SensorLocation.UnderTollBar:
            return self.sensors[1]
        elif location == SensorLocation.BehindTollBar:
            return self.sensors[2]
        else:
            print("Unrecognized sensor location!")

    def isVehicleBeforeTollBar(self):
        return (self.getSensorByLocation(SensorLocation.BeforeTollBar).value and 
                not self.getSensorByLocation(SensorLocation.UnderTollBar).value)
    
    def isVehicleUnderTollBar(self):
        return self.getSensorByLocation(SensorLocation.UnderTollBar).value
    
    def isVehicleBehindTollBar(self):
        return (not self.getSensorByLocation(SensorLocation.UnderTollBar).value and
                self.getSensorByLocation(SensorLocation.BehindTollBar).value)
    
    def isThereNoVehicleNearTollBar(self):
        return (not self.getSensorByLocation(SensorLocation.BeforeTollBar).value and 
                not self.getSensorByLocation(SensorLocation.UnderTollBar).value and
                not self.getSensorByLocation(SensorLocation.BehindTollBar).value)
    
    def updateSensors(self):
        for sensor in self.sensors:
            sensor.value = GPIO.input(sensor.port)
    
    def openBarrier(self):
        if self.barrier.state == BarrierState.Open:
            return
        servo = GPIO.PWM(self.barrier.port, 50) # GPIO as PWM output, with 50Hz frequency
        servo.start(0) # generate PWM signal with 7.5% duty cycle
        servo.ChangeDutyCycle(7.5) # change duty cycle for getting the servo position to 90
        self.barrier.state = BarrierState.Open
        self.startTimerForBarrier = time.perf_counter()

    
    def closeBarrier(self):
        if self.barrier.state == BarrierState.Closed:
            return
        if time.perf_counter() - self.startTimerForBarrier >= self.openGateTime:
            servo = GPIO.PWM(self.barrier.port, 50) # GPIO as PWM output, with 50Hz frequency
            servo.start(0) # generate PWM signal with 7.5% duty cycle
            servo.ChangeDutyCycle(-7.5) # change duty cycle for getting the servo position to -90
            self.barrier.state = BarrierState.Closed
            self.startTimerForBarrier = 0
