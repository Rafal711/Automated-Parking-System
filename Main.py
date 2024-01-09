import AutomatedParkingSystem
from AutomatedParkingSystem import max_capacity
from DataBaseManager import *
import pandas as pd
#Flask
from flask import Flask, jsonify, render_template
import numpy as np

app = Flask(__name__)
database = ParkingDB()

def getOccupancyData():
    currently_parked = database.getNumberOfCarsInAParkingLot()
    free = max_capacity - currently_parked
    occupancy_percentage = currently_parked / max_capacity * 100

    return currently_parked, free, occupancy_percentage
    

@app.route("/", methods=("POST", "GET"))
def home_screen():
    parked, free, percentage = getOccupancyData()
    return render_template("home.html", parked=parked, free=free, percentage=percentage)

@app.route("/stats", methods=("POST", "GET"))
def show_stats():
    parked, free, percentage = getOccupancyData()
    mapper_results, column_names = database.getParkedCarsTable()
    df = pd.DataFrame.from_records(mapper_results)
    if len(df) > 0:
        df.columns = column_names
    return render_template("stats.html", table_html=[df.to_html(classes='data', header='true')], 
                           last_refresh_time=datetime.now().replace(microsecond=0),
                           parked=parked, free=free, percentage=percentage)

if __name__ == "__main__":
    print("Automated Parking System")
    app.run(debug=True)
