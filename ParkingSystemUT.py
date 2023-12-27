import unittest
from CameraManager import CameraManager
from TollBarManager import SensorLocation, Sensor, BarrierState, Barrier, TollBarManager
from AutomatedParkingSystem import AutomatedParkingSystem
import Mock.GPIO as GPIO
from contextlib import contextmanager
import threading
import _thread
import time
import cv2
import os


# source: https://stackoverflow.com/questions/366682/how-to-limit-execution-time-of-a-function-call/37648512#37648512
class TimeoutException(Exception):
    def __init__(self, msg=''):
        self.msg = msg

@contextmanager
def time_limit(seconds, msg=''):
    timer = threading.Timer(seconds, lambda: _thread.interrupt_main())
    timer.start()
    try:
        yield
    except KeyboardInterrupt:
        raise TimeoutException("Timed out for operation {}".format(msg))
    finally:
        # if the action ends in specified time, timer is canceled
        timer.cancel()


class TestCameraManager(unittest.TestCase):

    def testPlateNumberRecognition(self):
        cameraManager = CameraManager(['pl', 'en'])
        expectedPlateNumbers = ['PO 156VN', 'HR.26 BR 9044', 'WY 8686W', 'WY 726XE']
        for i in range(4):
            image = cv2.imread(f'testData/vehicle{i}.jpg')
            plateNumber = cameraManager.getVehiclePlateNumber(image)
            self.assertEqual(plateNumber, expectedPlateNumbers[i])
    
    def testCameraPicturesTaking(self):
        cameraManager = CameraManager(['pl', 'en'])
        image = cameraManager.takePhoto()
        # cv2.imwrite("test_image.png", image)
        # wasPhotoTaken = os.path.exists("test_image.png")
        # self.assertTrue(wasPhotoTaken, "Photo was not taken")


class TestTollBarManager(unittest.TestCase):
    def testBarrierSensorsLogic(self):
        barrierManager = TollBarManager()
        # Car before barrier
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = True
        self.assertTrue(barrierManager.isVehicleBeforeTollBar(), "No vehicle before barrier")
        # Car under barrier
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = False
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = True
        self.assertTrue(barrierManager.isVehicleUnderTollBar(), "No vehicle under barrier")
        # Car entered the parking lot
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = False
        barrierManager.getSensorByLocation(SensorLocation.BehindTollBar).value = True
        self.assertTrue(barrierManager.isVehicleBehindTollBar(), "No vehicle behind barrier")
        # No car near barrier
        barrierManager.getSensorByLocation(SensorLocation.BehindTollBar).value = False
        self.assertTrue(barrierManager.isThereNoVehicleNearTollBar(), "Detected Vehicle near barrier")
    
    def testBarrierAsServoLogic(self):
        barrierManager = TollBarManager()
        barrierManager.openBarrier()
        barrierExpectedDegValue = 90
        self.assertEqual(barrierManager.barrier.postition, barrierExpectedDegValue)
        # Checking timer, barrier should not be closed
        barrierManager.closeBarrier() 
        self.assertEqual(barrierManager.barrier.postition, barrierExpectedDegValue)
        # Wait the preset number of seconds
        time.sleep(barrierManager.openGateTime)
        barrierManager.closeBarrier()
        
    def testServoLogicWhenCarUnderTollBar(self):
        barrierManager = TollBarManager()
        barrierManager.openBarrier() # barrier position = 90 deg
        with time_limit(barrierManager.openGateTime + 2):
           barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = True
           barrierManager.closeBarrier()
        self.assertEqual(barrierManager.barrier.postition, 90) # barrier should not be closed
        

class TestAutomatedParkingSystem(unittest.TestCase):
    def testCarEntersParkingLotScenario(self):
        automatedParkingSys = AutomatedParkingSystem()
        barrierManager = automatedParkingSys.barrierHandler

        # scenario step 1: No car near barrier
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar()
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        #TODO no new car in DB

        # scenario step 2: Car before barrier
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = True
        dummyCarPlateNumber1 = 'PO 156VN'
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 90)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Open)
        #TODO no new car in DB

        # scenario step 3: Car under barrier (new car before barrier, SensorLocation.BeforeTollBar still true)
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = True
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 90)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Open)
        #TODO no new car in DB

        # scenario step 4: Car behind barrier
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = False
        barrierManager.getSensorByLocation(SensorLocation.BehindTollBar).value = True
        # Wait the preset number of seconds (fulfil timer condition)
        time.sleep(barrierManager.openGateTime)
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 0)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        #TODO new car in DB, compare with dummyCarPlateNumber1

        #TODO scenario step 5: new Car behind barrier [alternative]


if __name__ == '__main__':
    unittest.main()
