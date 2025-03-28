import os
import pandas as pd
import joblib
import numpy as np
import mysql.connector
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration 
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Set your MySQL password here if needed
    "database": "rakusensdatabase"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"DB Connection Error: {err}")
        return None

# Fetch the latest row from the specified table (line4 or line5)
def fetch_latest_data(line):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT * FROM `{line}` ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        return row
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# Process a sensor's actual value against its Prophet model predictions
def process_sensor(sensor, line, actual):
    model_path = os.path.join("models", line, f"prophet_{sensor}.pkl")
    print(f"Looking for model at: {model_path}")
    print(os.path.abspath(model_path))  # Full absolute path for debugging


    if not os.path.exists(model_path):
        return {
            "value": round(actual, 2),
            "status": "no-model"
        }
    try:
        model = joblib.load(model_path)
        now = datetime.now()
        df_future = pd.DataFrame({"ds": [now]})
        df_future["ds"] = df_future["ds"].dt.tz_localize(None)
        forecast = model.predict(df_future)
        expected = forecast.iloc[0]["yhat"]
        lower = forecast.iloc[0]["yhat_lower"]
        upper = forecast.iloc[0]["yhat_upper"]
        # Determine traffic light status dynamically
        if lower <= actual <= upper:
            status = "green"
        elif abs(actual - upper) <= 10 or abs(actual - lower) <= 10:
            status = "amber"
        else:
            status = "red"
        return {
            "value": round(actual, 2),
            "expected": round(expected, 2),
            "lower": round(lower, 2),
            "upper": round(upper, 2),
            "status": status
        }
    except Exception as e:
        print(f"Error processing sensor {sensor}: {e}")
        return {
            "value": round(actual, 2),
            "status": "error"
        }

# API endpoint to get live data with ML anomaly detection for the selected line
@app.route('/api/live-data/<line>', methods=['GET'])
def live_data(line):
    if line not in ["line4", "line5"]:
        return jsonify({"success": False, "error": "Invalid line specified"}), 400

    row = fetch_latest_data(line)
    if not row:
        return jsonify({"success": False, "error": "No data available"}), 404

    timestamp = row.get("timestamp")
    result = {
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(timestamp, datetime) else timestamp
    }

    # Process all sensor columns that start with "r"
    sensors = [col for col in row.keys() if col.startswith("r")]
    for sensor in sensors:
        raw_val = row.get(sensor)
        if raw_val is None:
            result[sensor] = {"value": None, "status": "no-data"}
        else:
            try:
                actual = float(raw_val)
                result[sensor] = process_sensor(sensor, line, actual)
            except Exception as e:
                print(f"Error converting sensor {sensor} value: {e}")
                result[sensor] = {"value": None, "status": "error"}
    return jsonify({"success": True, "data": result})

@app.route('/')
def home():
    return jsonify({
        "message": "Rakusens ML API is running",
        "endpoints": {
            "/api/live-data/<line>": "Returns live sensor values with ML anomaly detection"
        }
    })

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
