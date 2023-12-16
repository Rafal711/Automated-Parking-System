import AutomatedParkingSystem
from DataBaseManager import *
import pandas as pd
#Flask
from flask import Flask, jsonify, render_template
import numpy as np

app = Flask(__name__)
database = ParkingDB()

@app.route("/", methods=("POST", "GET"))
def home_screen():
    return render_template("home.html")

@app.route("/stats", methods=("POST", "GET"))
def show_stats():
    mapper_results, column_names = database.getParkedCarsTable()
    df = pd.DataFrame.from_records(mapper_results)
    if len(df) > 0:
        df.columns = column_names
    return render_template("stats.html", table_html=[df.to_html(classes='data', header='true')], last_refresh_time=datetime.now().replace(microsecond=0))

if __name__ == "__main__":
    print("Automated Parking System")
    app.run(debug=True)
