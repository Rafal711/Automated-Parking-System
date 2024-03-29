from CameraManager import CameraManager
from TollBarManager import TollBarManager, BarrierState
from DataBaseManager import *

max_capacity = 100

class AutomatedParkingSystem:
    def __init__(self) -> None:
        self.cameraHandler = CameraManager(['pl', 'en'])
        self.barrierHandler = TollBarManager()
        self.parkingDb = ParkingDB()

    def runEntranceGate(self):
        vehiclePlateNumber = None
        while True:
            if self.barrierHandler.barrier.state == BarrierState.Closed and self.barrierHandler.isVehicleBeforeTollBar():
                carPhoto = self.cameraHandler.takePhoto()
                if carPhoto is None:
                    continue
                vehiclePlateNumber = self.cameraHandler.getVehiclePlateNumber(carPhoto)
                self.barrierHandler.openBarrier()
            if self.barrierHandler.barrier.state == BarrierState.Open:
                self.barrierHandler.closeBarrier()
                if self.barrierHandler.isVehicleBehindTollBar():
                    self.parkingDb.addCarEntryRecord(vehiclePlateNumber)
            self.barrierHandler.updateSensors()
    
    def runExitGate(self):
        vehiclePlateNumber = None
        while True:
            if self.barrierHandler.barrier.state == BarrierState.Closed and self.barrierHandler.isVehicleBeforeTollBar():
                carPhoto = self.cameraHandler.takePhoto()
                if carPhoto is None:
                    continue
                vehiclePlateNumber = self.cameraHandler.getVehiclePlateNumber(carPhoto)
                if self.parkingDb.wasFeePaid(vehiclePlateNumber):
                    self.barrierHandler.openBarrier()
            if self.barrierHandler.barrier.state == BarrierState.Open:
                self.barrierHandler.closeBarrier()
                if self.barrierHandler.isVehicleBehindTollBar():
                    self.parkingDb.releaseCarFromDb(vehiclePlateNumber)
            self.barrierHandler.updateSensors()
    
    def executeEntranceGateLogicOnceWithDummyCar(self, dummyVehiclePlateNumber=None):
        executeOnce = True
        while executeOnce:
            if self.barrierHandler.barrier.state == BarrierState.Closed and self.barrierHandler.isVehicleBeforeTollBar():
                self.barrierHandler.openBarrier()
            if self.barrierHandler.barrier.state == BarrierState.Open:
                self.barrierHandler.closeBarrier()
                if self.barrierHandler.isVehicleBehindTollBar():
                    self.parkingDb.addCarEntryRecord(dummyVehiclePlateNumber)
            self.barrierHandler.updateSensors()
            executeOnce = False
    
    def executeExitGateLogicOnceWithDummyCar(self, dummyVehiclePlateNumber=None):
        executeOnce = True
        while executeOnce:
            if self.barrierHandler.barrier.state == BarrierState.Closed and self.barrierHandler.isVehicleBeforeTollBar():
                if self.parkingDb.wasFeePaid(dummyVehiclePlateNumber):
                    self.barrierHandler.openBarrier()
            if self.barrierHandler.barrier.state == BarrierState.Open:
                self.barrierHandler.closeBarrier()
                if self.barrierHandler.isVehicleBehindTollBar():
                    self.parkingDb.releaseCarFromDb(dummyVehiclePlateNumber)
            self.barrierHandler.updateSensors()
            executeOnce = False
