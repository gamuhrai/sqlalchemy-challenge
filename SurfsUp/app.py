# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).\
    order_by(func.count(Measurement.station).desc()).all()
most_active_station_id = most_active_station[0]
#most_active_station_id = str(most_active_station_id)
most_active_station_id[0]
#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Convert the query results from your precipitation analysis 
    (i.e. retrieve only the last 12 months of data) to a dictionary"""
    # Query last 12 months
    query_result_last_12 = session.query(Measurement.station, Measurement.date, Measurement.prcp, Measurement.tobs).\
        filter(Measurement.date > '2016-08-18', Measurement.station == most_active_station_id[0]).\
        order_by(Measurement.date).all()

    session.close()

    precipitation_data = [
        {
            "station": station,
            "date": date,
            "prcp": prcp,
            "tobs": tobs
        }
        for station, date, prcp, tobs in query_result_last_12
    ]

    # Return the precipitation data as JSON
    return jsonify(precipitation_data)


@app.route("/api/v1.0/stations")
def station():
    # Create a session (link) from Python to the DB
    session = Session(engine)

    # Query the list of stations
    station_data = session.query(Measurement.station).distinct().all()

    session.close()

    # Convert the query result to a list of station names
    stations = [row.station for row in station_data]

    # Return the list of stations as JSON
    return jsonify(stations)


@app.route("/api/v1.0/tobs")
def get_temperature_observations():
    # Create a session (link) from Python to the DB
    session = Session(engine)

    # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()
    most_active_station_id = most_active_station[0]

    # Calculate the date one year ago from the last date in the dataset
    last_date = session.query(Measurement.date).\
        filter(Measurement.station == most_active_station_id).\
        order_by(Measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(last_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the temperature observations for the most active station for the previous year
    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id, Measurement.date >= one_year_ago).\
        order_by(Measurement.date).all()

    session.close()

    # Convert the query result to a list of dictionaries
    temperature_observations = [
        {"date": date, "tobs": tobs}
        for date, tobs in temperature_data
    ]

    # Return the list of temperature observations as JSON
    return jsonify(temperature_observations)

# Define the route for a start date only (e.g., /api/v1.0/yyyy-mm-dd)
@app.route("/api/v1.0/<start>")
def temperature_start(start):
    # Create a session (link) from Python to the DB
    session = Session(engine)

    # Convert the start date string to a datetime object
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")

    # Query the minimum, average, and maximum temperatures from the start date to the end of the dataset
    temperature_data = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date).all()

    session.close()

    # Convert the query result to a list of dictionaries with keys (TMIN, TAVG, TMAX)
    temperature_summary = [{
        "TMIN": temperature_data[0][0],
        "TAVG": temperature_data[0][1],
        "TMAX": temperature_data[0][2]
    }]

    # Return the temperature summary as JSON
    return jsonify(temperature_summary)


# Define the route for a start and end date range (e.g., /api/v1.0/yyyy-mm-dd/yyyy-mm-dd)
@app.route("/api/v1.0/<start>/<end>")
def temperature_start_end(start, end):
    # Create a session (link) from Python to the DB
    session = Session(engine)

    # Convert the start and end date strings to datetime objects
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end, "%Y-%m-%d")

    # Query the minimum, average, and maximum temperatures for the specified date range
    temperature_data = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date, Measurement.date <= end_date).all()

    session.close()

    # Convert the query result to a list of dictionaries with keys (TMIN, TAVG, TMAX)
    temperature_summary = [{
        "TMIN": temperature_data[0][0],
        "TAVG": temperature_data[0][1],
        "TMAX": temperature_data[0][2]
    }]

    # Return the temperature summary as JSON
    return jsonify(temperature_summary)


if __name__ == '__main__':
    app.run(debug=True)
