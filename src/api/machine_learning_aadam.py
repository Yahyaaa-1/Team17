import os
import pandas as pd
import joblib
import mysql.connector
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import time

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, config):
        self.config = config
    
    def get_connection(self):
        """Establish connection to MySQL database"""
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as err:
            print(f"DB Connection Error: {err}")
            return None
    
    def setup_forecast_table(self, conn, line):
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
    
    def store_forecasts(self, conn, line, sensor, timestamp, forecast):
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

class ForecastModel:
    """Handles model loading and forecasting"""
    
    def __init__(self, script_dir):
        self.script_dir = script_dir
    
    def detect_sensors(self, line):
        """Detect available sensor models for a line"""
        model_dir = os.path.join(self.script_dir, "models", line)
        sensors = []
        if os.path.exists(model_dir):
            for file in os.listdir(model_dir):
                if file.startswith("prophet_r") and file.endswith(".pkl"):
                    sensor_num = file.split("_r")[1].split(".pkl")[0]
                    sensors.append(f"r{sensor_num}")
        return sorted(sensors)
    
    def load_model_and_forecast(self, model_path, timestamp):
        """Load a Prophet model and forecast for a given timestamp"""
        try:
            model = joblib.load(model_path)
            future_df = pd.DataFrame({"ds": [timestamp]})
            forecast = model.predict(future_df)
            return forecast[["yhat", "yhat_lower", "yhat_upper"]].iloc[0]
        except Exception as e:
            print(f"Forecast error for {model_path}: {str(e)}")
            return None

class ForecastGenerator:
    """Main class that orchestrates the forecasting process"""
    
    def __init__(self, db_config, script_dir, start_time, interval, duration):
        self.db_manager = DatabaseManager(db_config)
        self.forecast_model = ForecastModel(script_dir)
        self.start_time = start_time
        self.interval = interval
        self.duration = duration
    
    def generate_timestamps(self):
        """Generate all timestamps for forecasting"""
        return [self.start_time + i * self.interval 
               for i in range(int(self.duration / self.interval) + 1)]
    
    def process_line(self, line):
        """Process all sensors for a single line"""
        start_time = time.time()
        
        sensors = self.forecast_model.detect_sensors(line)
        if not sensors:
            print(f"No sensor models found for {line}")
            return
        
        conn = self.db_manager.get_connection()
        if not conn:
            return
            
        # Setup table for this line
        self.db_manager.setup_forecast_table(conn, line)
        
        timestamps = self.generate_timestamps()
        print(f"\nProcessing {len(sensors)} sensors for {line}...")
        
        for sensor in sensors:
            model_path = os.path.join(self.forecast_model.script_dir, "models", line, 
                                    f"prophet_{sensor}.pkl")
            
            for timestamp in timestamps:
                forecast = self.forecast_model.load_model_and_forecast(model_path, timestamp)
                if forecast is not None:
                    self.db_manager.store_forecasts(conn, line, sensor, timestamp, forecast)
        
        conn.close()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken to process {line}: {elapsed_time:.2f} seconds")
    
    def generate_and_store_forecasts(self):
        """Generate forecasts for all lines and store in database"""
        for line in ["line4", "line5"]:
            self.process_line(line)
        print("\nForecast generation complete!")

# Configuration constants
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "rakusensdatabase"
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
START_TIME = datetime(2025, 4, 7, 14, 28, 0)
INTERVAL = timedelta(seconds=30)
DURATION = timedelta(hours=0.05)

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Create forecast generator instance
forecast_generator = ForecastGenerator(
    db_config=DB_CONFIG,
    script_dir=SCRIPT_DIR,
    start_time=START_TIME,
    interval=INTERVAL,
    duration=DURATION
)

@app.route('/forecast', methods=['GET'])
def get_forecast():
    """API endpoint to trigger forecast generation"""
    forecast_generator.generate_and_store_forecasts()
    return jsonify({"status": "success", "message": "Forecasts generated and stored"})

if __name__ == "__main__":
    forecast_generator.generate_and_store_forecasts()
    # To run as API: app.run(debug=True, use_reloader=False)