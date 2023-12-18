from sqlalchemy import create_engine, select, func, desc, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from datetime import datetime


# ------------------------------------------------------------------------------------

# modify this database address to what you have set in PgAdmin
db_string = "postgresql://postgres:admin@localhost:5432/Parking_lot_database"

engine = create_engine(db_string)

Base = declarative_base()

# ------------------------------------------------------------------------------------

class Parking_lot(Base):
    __tablename__ = 'Parking_lot'
    ID = Column(Integer, primary_key=True)
    Registration_number = Column(String)
    Entrance_time = Column(DateTime)
    Exit_time = Column(DateTime)
    Parking_time = Column(Integer)
    Fee = Column(Float)
    IsPaid = Column(Boolean)


    def __repr__(self):
        return "<Parking_lot(ID='{0}', Registration_number={1}, Entrance_time={2}, Exit_time={3}, Parking_time={4}, Fee={5}, IsPaid={6})>".format(
            self.ID, self.Registration_number, self.Entrance_time, self.Exit_time, self.Parking_time, self.Fee, self.IsPaid)
    
# ------------------------------------------------------------------------------------

class ParkingDB:
    def __init__(self):
        Base.metadata.create_all(engine)

        #initialize mapper operation
        self.metadata = MetaData()
        self.Parking_lot_table = Table(engine.table_names()[0], self.metadata , autoload=True, autoload_with=engine)


    # Database handling functions
    def addCarEntryRecord(self, registration):
        if not self.isCarParked(registration):
            ins = self.Parking_lot_table.insert().values(ID = self.getTableLength() + 1,
                                                    Registration_number = registration,
                                                    Entrance_time = datetime.now().replace(microsecond=0),
                                                    Exit_time = None,
                                                    Parking_time = None,
                                                    Fee = None,
                                                    IsPaid = False)
            result = engine.execute(ins)
        else:
            print("Car with given registration number is already parked!")
            return None


    def updateParkingTime(self, id):
        if id > self.getTableLength():
            return None
        
        # add parking time in minutes
        mapper_stmt = select(self.Parking_lot_table.columns.Entrance_time, self.Parking_lot_table.columns.Exit_time).\
                where(self.Parking_lot_table.columns.ID == id)

        result = engine.execute(mapper_stmt).fetchall()
        minutes = (result[0][1] - result[0][0]).total_seconds() / 60

        upd_parking_time = self.Parking_lot_table.update().\
                    where(self.Parking_lot_table.columns.ID == id).\
                    values(Parking_time = minutes)
        engine.execute(upd_parking_time)

        return minutes


    def updatePaymentStatus(self, registration, paid = True):
        id = self.findLastIdByRegistration(registration)
        if id > self.getTableLength():
            return None
        
        if id is not None:
            upd_payment_status = self.Parking_lot_table.update().\
                        where(self.Parking_lot_table.columns.ID == id).\
                        values(IsPaid = paid)
            engine.execute(upd_payment_status)
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
        engine.execute(upd_fee)

        return fee


    def updateAtExit(self, registration):
        id = self.findLastIdByRegistration(registration)

        # update exit time
        if id is not None:
            upd_exit = self.Parking_lot_table.update().\
                    where(self.Parking_lot_table.columns.ID == id).\
                    values(Exit_time = datetime.now().replace(microsecond=0))

            engine.execute(upd_exit)
        else:
            print("W bazie nie istnieje dany numer")
            return None
        
        minutes = self.updateParkingTime(id)
        self.updateFee(id, minutes)


    def getTableLength(self):
        count_stmt = select(func.count(self.Parking_lot_table.columns.ID))
        return engine.execute(count_stmt).fetchall()[0][0]


    def findLastIdByRegistration(self, registration):
        mapper_stmt = select(self.Parking_lot_table.columns.ID).\
                    where(self.Parking_lot_table.columns.Registration_number == registration).\
                    order_by(desc(self.Parking_lot_table.columns.ID)).\
                    limit(1)
        
        result = engine.execute(mapper_stmt).fetchall()

        if result:
            return result[0][0]
        else:
            return None


    def isCarParked(self, registration):
        id = self.findLastIdByRegistration(registration)

        if id is not None:
            mapper_stmt = select(self.Parking_lot_table.columns.ID).\
                    where(self.Parking_lot_table.columns.ID == id and self.Parking_lot_table.columns.Exit_time == None)
            result = engine.execute(mapper_stmt).fetchall()

            if result:
                return True
        return False


    def getFee(self, registration):
        id = self.findLastIdByRegistration(registration)

        mapper_stmt = select(self.Parking_lot_table.columns.Fee).\
                    where(self.Parking_lot_table.columns.ID == id)
        
        result = engine.execute(mapper_stmt).fetchall()

        if result:
            return result[0][0]
        else:
            return None


    def getParkingTimeInMinutes(self, registration):
        id = self.findLastIdByRegistration(registration)

        mapper_stmt = select(self.Parking_lot_table.columns.Parking_time).\
                    where(self.Parking_lot_table.columns.ID == id)
        
        result =  engine.execute(mapper_stmt).fetchall()

        if result:
            return result[0][0]
        else:
            return None


    def getParkingTimeInHours(self, registration):
        minutes = self.getParkingTimeInMinutes(registration)
        return round(minutes / 60, 2)


    def getNumberOfParkedCars(self):
        mapper_stmt = select(func.count(self.Parking_lot_table.columns.ID)).\
                    where(self.Parking_lot_table.columns.Exit_time == None)

        result =  engine.execute(mapper_stmt).fetchall()

        if result:
            return result[0][0]
        else:
            return None

    def getParkedCarsTable(self):
        mapper_stmt = select([self.Parking_lot_table.columns.Registration_number, self.Parking_lot_table.columns.Entrance_time]).\
                    where(self.Parking_lot_table.columns.Exit_time == None)

        results =  engine.execute(mapper_stmt)
        columns = results.keys()
        results = results.fetchall()
        return results, columns
