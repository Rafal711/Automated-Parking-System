import unittest
from CameraManager import CameraManager
from TollBarManager import SensorLocation, Sensor, BarrierState, Barrier, TollBarManager
from AutomatedParkingSystem import AutomatedParkingSystem
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
        initalNumberOfParkedCars = automatedParkingSys.parkingDb.getNumberOfCarsInAParkingLot()

        # scenario step 1: No car near barrier
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar()
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        # no new car in DB
        self.assertEqual(initalNumberOfParkedCars, automatedParkingSys.parkingDb.getNumberOfCarsInAParkingLot())

        # scenario step 2: Car before barrier
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = True
        dummyCarPlateNumber1 = 'PO 156VN'
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 90)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Open)
        # no new car in DB
        self.assertEqual(initalNumberOfParkedCars, automatedParkingSys.parkingDb.getNumberOfCarsInAParkingLot())

        # scenario step 3: Car under barrier (new car before barrier, SensorLocation.BeforeTollBar still true)
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = True
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 90)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Open)
        # no new car in DB
        self.assertEqual(initalNumberOfParkedCars, automatedParkingSys.parkingDb.getNumberOfCarsInAParkingLot())

        # scenario step 4: Car behind barrier
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = False
        barrierManager.getSensorByLocation(SensorLocation.BehindTollBar).value = True
        # Wait the preset number of seconds (fulfil timer condition)
        time.sleep(barrierManager.openGateTime)
        automatedParkingSys.executeEntranceGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 0)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        # new car in DB, compare with dummyCarPlateNumber1
        self.assertTrue(automatedParkingSys.parkingDb.isCarParked(dummyCarPlateNumber1))
        #TODO scenario step 5: new Car behind barrier [alternative]
    
    def testCarExitsParkingLotScenario(self):
        automatedParkingSys = AutomatedParkingSystem()
        barrierManager = automatedParkingSys.barrierHandler
        parkingDb = automatedParkingSys.parkingDb
        dummyCarPlateNumber1 = 'WY 8686W'
        parkingDb.addCarEntryRecord(dummyCarPlateNumber1) # added dummy car to parking lot

        # scenario step 1: No car near barrier
        automatedParkingSys.executeExitGateLogicOnceWithDummyCar()
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        #car still in Db (no release)
        self.assertTrue(automatedParkingSys.parkingDb.isCarParked(dummyCarPlateNumber1))

        # scenario step 2: Car before barrier (fee not paid)
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = True
        automatedParkingSys.executeExitGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 0)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        # car still in Db (no release - fee not paid)
        self.assertFalse(automatedParkingSys.parkingDb.wasFeePaid(dummyCarPlateNumber1))
        self.assertTrue(automatedParkingSys.parkingDb.isCarParked(dummyCarPlateNumber1))


        # scenario step 3: Car before barrier (fee paid)
        # end parking time and calculate fee
        automatedParkingSys.parkingDb.updateParkingEndTime(dummyCarPlateNumber1)
        # update fee payment status - paid
        automatedParkingSys.parkingDb.updatePaymentStatus(dummyCarPlateNumber1)
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = True
        automatedParkingSys.executeExitGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 90)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Open)
        # car still in Db (no release - fee paid)
        self.assertTrue(automatedParkingSys.parkingDb.wasFeePaid(dummyCarPlateNumber1))
        self.assertTrue(automatedParkingSys.parkingDb.isCarParked(dummyCarPlateNumber1))

        # scenario step 4: Car under barrier
        barrierManager.getSensorByLocation(SensorLocation.BeforeTollBar).value = False
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = True
        automatedParkingSys.executeExitGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 90)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Open)
        # car still in Db (no release)
        self.assertTrue(automatedParkingSys.parkingDb.isCarParked(dummyCarPlateNumber1))

        # scenario step 5: Car behind barrier
        barrierManager.getSensorByLocation(SensorLocation.UnderTollBar).value = False
        barrierManager.getSensorByLocation(SensorLocation.BehindTollBar).value = True
        # Wait the preset number of seconds (fulfil timer condition)
        time.sleep(barrierManager.openGateTime)
        automatedParkingSys.executeExitGateLogicOnceWithDummyCar(dummyCarPlateNumber1)
        self.assertEqual(barrierManager.barrier.postition, 0)
        self.assertEqual(barrierManager.barrier.state, BarrierState.Closed)
        # check if car was released from Db (outside parking lot)
        self.assertFalse(automatedParkingSys.parkingDb.isCarParked(dummyCarPlateNumber1))


if __name__ == '__main__':
    unittest.main()
