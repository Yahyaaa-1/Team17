import os
import pandas as pd
import joblib
import mysql.connector
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import time 

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "rakusensdatabase"
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
START_TIME = datetime(2025, 4, 11, 0, 38, 0)
INTERVAL = timedelta(seconds=30)
DURATION = timedelta(hours=0.25)

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"DB Connection Error: {err}")
        return None

def detect_active_sensors(conn, line):
    cursor = conn.cursor()
    
    cursor.execute(f"SHOW COLUMNS FROM {line} LIKE 'r%'")
    db_sensors = [col[0] for col in cursor.fetchall() if col[0].startswith('r')]
    
    model_dir = os.path.join(SCRIPT_DIR, "models", line)
    model_sensors = []
    if os.path.exists(model_dir):
        model_sensors = [
            f"r{file.split('_r')[1].split('.pkl')[0]}" 
            for file in os.listdir(model_dir) 
            if file.startswith("prophet_r") and file.endswith(".pkl")
        ]
    
    return sorted(list(set(db_sensors) & set(model_sensors)))

def setup_forecast_table(conn, line):
    cursor = conn.cursor()
    table_name = f"forecasted{line}"
    
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        print(f"Cleared existing table: {table_name}")
    else:
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
    try:
        model = joblib.load(model_path)
        future_df = pd.DataFrame({"ds": [timestamp]})
        forecast = model.predict(future_df)
        return forecast[["yhat", "yhat_lower", "yhat_upper"]].iloc[0]
    except Exception as e:
        print(f"Forecast error for {model_path}: {str(e)}")
        return None

def store_forecasts(conn, line, sensor, timestamp, forecast):
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
    conn = get_db_connection()
    if not conn:
        return
    
    for line in ["line4", "line5"]:
        start_time = time.time()
        
        sensors = detect_active_sensors(conn, line)
        if not sensors:
            print(f"No active sensor models found for {line}")
            continue
            
        setup_forecast_table(conn, line)
        timestamps = [START_TIME + i * INTERVAL 
                     for i in range(int(DURATION / INTERVAL) + 1)]
        
        print(f"\nProcessing {len(sensors)} active sensors for {line}...")
        
        for sensor in sensors:
            model_path = os.path.join(SCRIPT_DIR, "models", line, 
                                    f"prophet_{sensor}.pkl")
            
            for timestamp in timestamps:
                forecast = load_model_and_forecast(model_path, timestamp)
                if forecast is not None:
                    store_forecasts(conn, line, sensor, timestamp, forecast)

        end_time = time.time()
        print(f"Time taken to process {line}: {end_time - start_time:.2f} seconds")
    
    conn.close()
    print("\nForecast generation complete!")

@app.route('/forecast', methods=['GET'])
def get_forecast():
    generate_and_store_forecasts()
    return jsonify({"status": "success", "message": "Forecasts generated and stored"})

if __name__ == "__main__":
    generate_and_store_forecasts()