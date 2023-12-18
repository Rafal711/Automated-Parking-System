from CameraManager import CameraManager
from TollBarManager import TollBarManager, BarrierState
from DataBaseManager import ParkingDB

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
                if not self.barrierHandler.isVehicleUnderTollBar():
                    self.barrierHandler.closeBarrier()
                if self.barrierHandler.isVehicleBehindTollBar():
                    self.parkingDb.addCarEntryRecord(vehiclePlateNumber)
            self.barrierHandler.updateSensors()
    
    def runExitGate(self):
        raise NotImplementedError
