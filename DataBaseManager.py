from sqlalchemy import create_engine, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float

# modify this
db_string = "postgresql://postgres:admin@localhost:5432/intelligent_parking"

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


    def __repr__(self):
        return "<Parking_lot(ID='{0}', Registration_number={1}, Entrance_time={2}, Exit_time={3}, Parking_time={4}, Fee={5})>".format(
            self.ID, self.Registration_number, self.Entrance_time, self.Exit_time, self.Parking_time, self.Fee)
    
# ------------------------------------------------------------------------------------

Base.metadata.create_all(engine)
