import os
import pandas as pd
import joblib
import mysql.connector
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import time 
# Flask App Configuration
app = Flask(__name__)
CORS(app)

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "rakusensdatabase"
}

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
START_TIME = datetime(2025, 4, 5, 1, 10, 0)
INTERVAL = timedelta(seconds=30)
DURATION = timedelta(hours=0.25)

def get_db_connection():
    """Establish connection to MySQL database"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"DB Connection Error: {err}")
        return None

def detect_sensors(line):
    """Detect available sensor models for a line"""
    model_dir = os.path.join(SCRIPT_DIR, "models", line)
    sensors = []
    if os.path.exists(model_dir):
        for file in os.listdir(model_dir):
            if file.startswith("prophet_r") and file.endswith(".pkl"):
                sensor_num = file.split("_r")[1].split(".pkl")[0]
                sensors.append(f"r{sensor_num}")
    return sorted(sensors)

def setup_forecast_table(conn, line):
    """Create or clear forecast table for a line"""
    cursor = conn.cursor()
    table_name = f"forecasted{line}"
    
    # Check if table exists
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    exists = cursor.fetchone()
    
    if exists:
        # Clear existing table
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        print(f"Cleared existing table: {table_name}")
    else:
        # Create new table
        cursor.execute(f"""
        CREATE TABLE {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sensor VARCHAR(10) NOT NULL,
            forecast_time DATETIME NOT NULL,
            forecast_value FLOAT NOT NULL,
            lower_bound FLOAT NOT NULL,
            upper_bound FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY (sensor, forecast_time)
        )
        """)
        print(f"Created new table: {table_name}")
    
    conn.commit()
    cursor.close()

def load_model_and_forecast(model_path, timestamp):
    """Load a Prophet model and forecast for a given timestamp"""
    try:
        model = joblib.load(model_path)
        future_df = pd.DataFrame({"ds": [timestamp]})
        forecast = model.predict(future_df)
        return forecast[["yhat", "yhat_lower", "yhat_upper"]].iloc[0]
    except Exception as e:
        print(f"Forecast error for {model_path}: {str(e)}")
        return None

def store_forecasts(conn, line, sensor, timestamp, forecast):
    """Store forecast in database"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"INSERT INTO forecasted{line} "
            "(sensor, forecast_time, forecast_value, lower_bound, upper_bound) "
            "VALUES (%s, %s, %s, %s, %s)",
            (sensor, timestamp, forecast['yhat'], 
             forecast['yhat_lower'], forecast['yhat_upper'])
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Database insert error: {err}")
    finally:
        cursor.close()

def generate_and_store_forecasts():
    """Generate forecasts for all lines and store in database"""
    conn = get_db_connection()
    if not conn:
        return
    
    # Process both lines
    for line in ["line4", "line5"]:
        
        start_time = time.time()  # Start timing

        sensors = detect_sensors(line)
        if not sensors:
            print(f"No sensor models found for {line}")
            continue
            
        # Setup table for this line
        setup_forecast_table(conn, line)
        
        # Generate timestamps
        timestamps = [START_TIME + i * INTERVAL 
                     for i in range(int(DURATION / INTERVAL) + 1)]
        
        print(f"\nProcessing {len(sensors)} sensors for {line}...")
        
        for sensor in sensors:
            model_path = os.path.join(SCRIPT_DIR, "models", line, 
                                    f"prophet_{sensor}.pkl")
            
            for timestamp in timestamps:
                forecast = load_model_and_forecast(model_path, timestamp)
                if forecast is not None:
                    store_forecasts(conn, line, sensor, timestamp, forecast)

        end_time = time.time()  # End timing
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        print(f"Time taken to process {line}: {elapsed_time:.2f} seconds")  # Print the time taken
    
    
    conn.close()
    print("\nForecast generation complete!")

@app.route('/forecast', methods=['GET'])
def get_forecast():
    """API endpoint to trigger forecast generation"""
    generate_and_store_forecasts()
    return jsonify({"status": "success", "message": "Forecasts generated and stored"})

if __name__ == "__main__":
    generate_and_store_forecasts()
    # To run as API: app.run(debug=True, use_reloader=False)