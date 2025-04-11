import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app import SimulationService, LogService
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash


class TestSimulationService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_log = MagicMock(spec=LogService)
        self.sim_service = SimulationService(self.mock_db, self.mock_log)
        
        # Add the required sensor ranges
        self.sim_service.SENSOR_RANGES_LINE4 = {
            "r01": {"avg": 129.10, "min": 16.00, "max": 258.00}
        }

    def test_sensor_reading_generation(self):
        reading = self.sim_service.generate_sensor_reading(
            'r01', self.sim_service.SENSOR_RANGES_LINE4
        )
        self.assertIsInstance(reading, float)
        self.assertGreaterEqual(reading, 16.0)
        self.assertLessEqual(reading, 258.0)
        print("Test sensor reading generation passed successfully.")

    @patch('time.localtime')  # Correct patching of time.localtime
    def test_timezone_offset(self, mock_localtime):
        """Test timezone offset calculation"""

        # Test for months April to October (should return +01)
        for month in range(4, 11):
            mock_localtime.return_value.tm_mon = month
            offset = self.sim_service.get_timezone_offset()
            self.assertEqual(offset, "+01", f"Failed for month {month}")

        # Test for months November to March (should return +00)
        for month in range(1, 4):
            mock_localtime.return_value.tm_mon = month
            offset = self.sim_service.get_timezone_offset()
            self.assertEqual(offset, "+00", f"Failed for month {month}")

        print("Test timezone offset calculation passed successfully.")

    def test_multiple_sensor_readings(self):
        """Test generation of multiple sensor readings"""
        
        # Define the sensor ranges directly in the method
        sensor_ranges_line4 = {
            "r01": {"avg": 129.10, "min": 16.00, "max": 258.00},
            "r02": {"avg": 264.81, "min": 18.00, "max": 526.00},
            "r03": {"avg": 255.77, "min": 17.00, "max": 476.00},
            "r04": {"avg": 309.04, "min": 13.00, "max": 554.00}
        }
        
        # List of sensors in the sensor range
        sensors = sensor_ranges_line4.keys()

        # Generate readings for each sensor and check the results
        for sensor in sensors:
            reading = self.sim_service.generate_sensor_reading(
                sensor, sensor_ranges_line4
            )
            
            # Ensure the reading is within the min and max range for the sensor
            min_value = sensor_ranges_line4[sensor]["min"]
            max_value = sensor_ranges_line4[sensor]["max"]
            self.assertIsInstance(reading, float)  # Ensure it's a float
            self.assertGreaterEqual(reading, min_value)  # Ensure the reading is >= min
            self.assertLessEqual(reading, max_value)  # Ensure the reading is <= max

        print("Test multiple sensor readings passed successfully.")

    @patch('threading.Thread')
    def test_simulation_start_stop(self, mock_thread):
        """Test simulation thread management"""

        # Test that calling start creates and starts a thread
        mock_thread.return_value = MagicMock(spec=Thread)
        
        # Call start and check if the thread is started
        self.sim_service.start()

        # Assert that a thread was created
        mock_thread.assert_called_once_with(target=self.sim_service.generate_temperature_readings, daemon=True)
        
        # Assert that the thread was started
        mock_thread.return_value.start.assert_called_once()

        # Now, test stop (it should not explicitly stop the thread as it's a daemon thread)
        # Call stop and check if it doesn't raise an error or do anything specific (since it's a daemon thread)
        self.sim_service.stop()

        # Since the `stop()` method doesn't explicitly stop the thread in this implementation,
        # there's no direct assertion here, but we can ensure it runs without errors.
        print("Test simulation start/stop passed successfully.")

    @patch('time.localtime')
    @patch.object(SimulationService, 'generate_sensor_reading')  # Mock generate_sensor_reading to return fixed values
    def test_insert_line_readings(self, mock_generate_reading, mock_localtime):
        """Test database insertion of readings"""

        # Define sensor ranges directly in the method
        sensor_ranges_line4 = {
            "r01": {"avg": 129.10, "min": 16.00, "max": 258.00},
            "r02": {"avg": 264.81, "min": 18.00, "max": 526.00}
        }

        # Set the mocked current time and timezone
        mock_localtime.return_value.tm_mon = 5  # May (for timezone offset +01)
        current_timestamp = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        timezone_offset = "+01"  # Simulating the timezone offset for May

        # Mock the sensor readings to return fixed values for r01 and r02
        mock_generate_reading.side_effect = [130.45, 267.87]  # These are the expected values for r01 and r02

        # Mock the database connection and cursor
        mock_connection = MagicMock()  # Mock the real database connection
        mock_cursor = MagicMock()  # Mock the cursor
        mock_connection.cursor.return_value = mock_cursor
        self.mock_db.get_connection.return_value = mock_connection  # Mock the database manager to return the mock connection

        # Define the sensors for line4 (as an example)
        sensors = ['r01', 'r02']

        # Call insert_line_readings with the correct parameter order
        self.sim_service.insert_line_readings(
            mock_connection,  # Pass the mock connection here
            mock_cursor,      # Pass the mock cursor here
            'line4',          # Line name
            sensors,          # Sensors list
            sensor_ranges_line4,  # Sensor ranges
            current_timestamp,    # Timestamp
            timezone_offset       # Timezone
        )

        # Expected query to be executed (strip out extra indentation/spacing)
        expected_query = """
            INSERT INTO line4
            (timestamp, timezone, r01, r02)
            VALUES (%s, %s, %s, %s)
        """
        
        # Normalize both the actual and expected query strings by stripping excess whitespace and newlines
        def normalize_query(query):
            # Remove extra spaces and normalize the string
            return " ".join(query.strip().split())

        # Normalize the expected and actual queries
        normalized_expected_query = normalize_query(expected_query)
        normalized_actual_query = normalize_query(mock_cursor.execute.call_args[0][0])

        # Ensure the query is executed with the correct parameters
        self.assertEqual(normalized_actual_query, normalized_expected_query)

        # Ensure the parameters passed to execute() match the expected values
        self.assertEqual(mock_cursor.execute.call_args[0][1], 
                        [current_timestamp, timezone_offset, 130.45, 267.87])

        # Ensure commit was called to persist the data
        mock_connection.commit.assert_called_once()  # Ensure commit was called on the actual connection object

        print("Test insert line readings passed successfully.")

    def test_reading_range_validation(self):
        """Test sensor readings stay within defined ranges"""
        
        # Define sensor ranges (e.g., for line4)
        sensor_ranges_line4 = {
            "r01": {"avg": 129.10, "min": 16.00, "max": 258.00},
            "r02": {"avg": 264.81, "min": 18.00, "max": 526.00},
            "r03": {"avg": 255.77, "min": 17.00, "max": 476.00},
            "r04": {"avg": 309.04, "min": 13.00, "max": 554.00}
        }

        # List of sensors to check
        sensors = sensor_ranges_line4.keys()

        for sensor in sensors:
            # Generate a sensor reading for the current sensor and ranges
            reading = self.sim_service.generate_sensor_reading(sensor, sensor_ranges_line4)
            
            # Get the min and max values for this sensor from the ranges
            min_value = sensor_ranges_line4[sensor]["min"]
            max_value = sensor_ranges_line4[sensor]["max"]

            # Assert that the reading is a float
            self.assertIsInstance(reading, float)
            
            # Assert that the reading is within the defined range
            self.assertGreaterEqual(reading, min_value, f"Reading for {sensor} is less than the minimum allowed value.")
            self.assertLessEqual(reading, max_value, f"Reading for {sensor} is greater than the maximum allowed value.")

        print("Test reading range validation passed successfully.")

if __name__ == '__main__':
    unittest.main()
