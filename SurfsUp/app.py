# Import the dependencies.
import datetime as dt
import numpy as np
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# Home page
@app.route("/")

def welcome():
    return (
        f"Welcome to my Climate App<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Last 12 months of precipitation data<br/>"
        f"/api/v1.0/stations - List of stations<br/>"
        f"/api/v1.0/tobs - Temperature observations of the most active station for the last year<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Temperature stats for a date range (YYYY-MM-DD)"
    )
    
# Precipitation data.
@app.route("/api/v1.0/precipitation")
def precipitation():
    
    # Calculate the last 12 months.
    f_date_str = session.query(func.max(measurement.date)).scalar()
    f_date = dt.datetime.strptime(f_date_str, "%Y-%m-%d")
    
    #Define 1 year ago
    year_ago = f_date - dt.timedelta(days=365)
    
    # Query the last 12 months of precip data.
    precip_data = session.query(measurement.date, measurement.prcp)\
        .filter(measurement.date >= year_ago.strftime("%Y-%m-%d"))\
        .all()
    
    # Convert the query results to a dictionary
    precip_dict = {date: prcp for date, prcp in precip_data}
    return jsonify(precip_dict)

# List of stations.
@app.route("/api/v1.0/stations")
def stations():
    # Find all station id's
    total_stations = session.query(station.station).all()
    # Convert to a list
    stations_list = list(np.ravel(total_stations))
    return jsonify(stations_list)


# Temperature observations of the most active station
@app.route("/api/v1.0/tobs")
def tobs():
    # Find the most active station
    most_active_stations = session.query(measurement.station, func.count(measurement.station))\
        .group_by(measurement.station)\
        .order_by(func.count(measurement.station).desc())\
        .first()[0]
    
    # Calculate the last 12 months.
    f_date = session.query(func.max(measurement.date)).scalar()
    f_date = dt.datetime.strptime(f_date, "%Y-%m-%d")
    year_ago = f_date - dt.timedelta(days=365)
    
    # Find the last 12 months for the most active station.
    results = session.query(measurement.date, measurement.tobs)\
        .filter(measurement.station == most_active_stations)\
        .filter(measurement.date >= year_ago.strftime("%Y-%m-%d"))\
        .all()
    
    # Convert to a list of dictionaries.
    temps = []
    for date, tobs in results:
        temps.append({"date": date, "tobs": tobs})
    
    return jsonify(temps)

# Temperature stats for a date range.
@app.route("/api/v1.0/<start>/<end>")
def temp_stats_start_end(start, end):
    # Find min, avg, and max temperatures for dates between the start and end date
    results = session.query(
        func.min(measurement.tobs),
        func.avg(measurement.tobs),
        func.max(measurement.tobs)
    ).filter(measurement.date >= start)\
     .filter(measurement.date <= end)\
     .all()
    
    # Unravel results into a list.
    stats = list(np.ravel(results))
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)