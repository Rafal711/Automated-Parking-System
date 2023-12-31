from sqlalchemy import create_engine, select, func, desc, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from datetime import datetime

Base = declarative_base()

class Parking_lot(Base):
    __tablename__ = 'Parking_lot'
    ID = Column(Integer, primary_key=True)
    Registration_number = Column(String)
    Entrance_time = Column(DateTime)
    End_time = Column(DateTime)
    Parking_duration = Column(Integer)
    Fee = Column(Float)
    IsPaid = Column(Boolean)
    Payment_time = Column(DateTime)
    Exit_time = Column(DateTime)


    def __repr__(self):
        return "<Parking_lot(ID='{0}', Registration_number={1}, Entrance_time={2}, End_time={3}, Parking_duration={4}, Fee={5}, IsPaid={6}, Payment_time={7}, Exit_time={8})>".format(
            self.ID, self.Registration_number, self.Entrance_time, self.End_time, self.Parking_duration, self.Fee, self.IsPaid, self.Payment_time, self.Exit_time)
    
# ------------------------------------------------------------------------------------

class ParkingDB:
    def __init__(self):
        # ------------------------------------------------------------------------------------
        # modify this database address to what you have set in PgAdmin
        # "db_driver://user:password@ip_adrress:port/db_name"
        self.db_string = "postgresql://postgres:admin@localhost:5432/Parking_lot_database"
        self.engine = create_engine(self.db_string)
        # ------------------------------------------------------------------------------------

        Base.metadata.create_all(self.engine)

        #initialize mapper operation
        self.metadata = MetaData()
        self.Parking_lot_table = Table(self.engine.table_names()[0], self.metadata , autoload=True, autoload_with=self.engine)


    # Database handling functions
    def addCarEntryRecord(self, registration):
        if not self.isCarParked(registration):
            ins = self.Parking_lot_table.insert().values(ID = self.getTableLength() + 1,
                                                    Registration_number = registration,
                                                    Entrance_time = datetime.now().replace(microsecond=0),
                                                    End_time = None,
                                                    Parking_duration = None,
                                                    Fee = None,
                                                    IsPaid = False,
                                                    Payment_time = None,
                                                    Exit_time = None)
            self.engine.execute(ins)
        else:
            print("Car with given registration number is already parked!")
            return None


    def updateParkingDuration(self, id):
        if id > self.getTableLength():
            return None
        
        # add parking duration in minutes
        mapper_stmt = select(self.Parking_lot_table.columns.Entrance_time, self.Parking_lot_table.columns.End_time).\
                where(self.Parking_lot_table.columns.ID == id)

        result = self.engine.execute(mapper_stmt).fetchall()
        minutes = (result[0][1] - result[0][0]).total_seconds() / 60

        upd_parking_duration = self.Parking_lot_table.update().\
                    where(self.Parking_lot_table.columns.ID == id).\
                    values(Parking_duration = minutes)
        self.engine.execute(upd_parking_duration)

        return minutes


    def updatePaymentStatus(self, registration, paid = True):
        id = self.findLastIdByRegistration(registration)
        
        if id is not None:
            upd_payment_status = self.Parking_lot_table.update().\
                        where(self.Parking_lot_table.columns.ID == id).\
                        values(IsPaid = paid, Payment_time=datetime.now().replace(microsecond=0))
            self.engine.execute(upd_payment_status)
        else:
            print("W bazie nie istnieje dany numer")
            return None


    def wasFeePaid(self, registration):
        id = self.findLastIdByRegistration(registration)
       
        if id is not None:
            mapper_stmt = select(self.Parking_lot_table.columns.IsPaid).\
                where(self.Parking_lot_table.columns.ID == id)
            result = self.engine.execute(mapper_stmt).fetchall()
            return result[0][0]
        else:
            print("W bazie nie istnieje dany numer")
            return None 


    def updateFee(self, id, minutes, price_per_hour = 2):
        if id > self.getTableLength():
            return None

        fee = round(minutes / 60 * price_per_hour, 2)

        upd_fee = self.Parking_lot_table.update().\
                    where(self.Parking_lot_table.columns.ID == id).\
                    values(Fee = fee)
        self.engine.execute(upd_fee)

        return fee


    def updateParkingEndTime(self, registration):
        id = self.findLastIdByRegistration(registration)

        # update End time
        if id is not None:
            upd_End = self.Parking_lot_table.update().\
                    where(self.Parking_lot_table.columns.ID == id).\
                    values(End_time = datetime.now().replace(microsecond=0))
            self.engine.execute(upd_End)
            
            minutes = self.updateParkingDuration(id)
            self.updateFee(id, minutes)
        else:
            print("W bazie nie istnieje dany numer")
            return None
        

    def releaseCarFromDb(self, registration):
        id = self.findLastIdByRegistration(registration)

        # exit time (car left the parking lot)
        if id is not None:
            upd_Exit = self.Parking_lot_table.update().\
                    where(self.Parking_lot_table.columns.ID == id).\
                    values(Exit_time = datetime.now().replace(microsecond=0))
            self.engine.execute(upd_Exit)
        else:
            print("W bazie nie istnieje dany numer")
            return None


    def getTableLength(self):
        count_stmt = select(func.count(self.Parking_lot_table.columns.ID))
        return self.engine.execute(count_stmt).fetchall()[0][0]


    def findLastIdByRegistration(self, registration):
        if registration is None:
            return None
        
        mapper_stmt = select(self.Parking_lot_table.columns.ID).\
                    where(self.Parking_lot_table.columns.Registration_number == registration).\
                    order_by(desc(self.Parking_lot_table.columns.ID)).\
                    limit(1)
        result = self.engine.execute(mapper_stmt).fetchall()

        if result:
            return result[0][0]
        else:
            return None


    def isCarParked(self, registration):
        id = self.findLastIdByRegistration(registration)

        if id is not None:
            mapper_stmt = select(self.Parking_lot_table.columns.ID).\
                    where(self.Parking_lot_table.columns.ID == id).\
                    where(self.Parking_lot_table.columns.Exit_time == None)
            result = self.engine.execute(mapper_stmt).fetchall()

            if result:
                return True
            
        return False


    def getFee(self, registration):
        id = self.findLastIdByRegistration(registration)

        if id is not None:
            mapper_stmt = select(self.Parking_lot_table.columns.Fee).\
                        where(self.Parking_lot_table.columns.ID == id)
            result = self.engine.execute(mapper_stmt).fetchall()

            if result is not None:
                return result[0][0]

        return None


    def getParkingDurationInMinutes(self, registration):
        id = self.findLastIdByRegistration(registration)

        mapper_stmt = select(self.Parking_lot_table.columns.Parking_duration).\
                    where(self.Parking_lot_table.columns.ID == id)
        result =  self.engine.execute(mapper_stmt).fetchall()

        if result is not None:
            return result[0][0]
        else:
            return None


    def getParkingDurationInHours(self, registration):
        minutes = self.getParkingDurationInMinutes(registration)
        return round(minutes / 60, 2)


    def getNumberOfCarsInAParkingLot(self):
        mapper_stmt = select(func.count(self.Parking_lot_table.columns.ID)).\
                    where(self.Parking_lot_table.columns.Exit_time == None)

        result =  self.engine.execute(mapper_stmt).fetchall()

        if result is not None:
            return result[0][0]
        else:
            return None


    def getParkedCarsTable(self):
        mapper_stmt = select([self.Parking_lot_table.columns.Registration_number, self.Parking_lot_table.columns.Entrance_time]).\
                    where(self.Parking_lot_table.columns.End_time == None)

        results =  self.engine.execute(mapper_stmt)
        columns = results.keys()
        results = results.fetchall()
        return results, columns
