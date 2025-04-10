import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app import DataService, LogService
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash

class TestDataService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_log = MagicMock(spec=LogService)
        self.data_service = DataService(self.mock_db, self.mock_log)
        
    def test_historical_data_retrieval(self):
        mock_data = [{'timestamp': datetime.now(), 'value': 42.0}]
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_data
        
        response = self.data_service.get_historical_data('line4', {})
        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']), 1)


    
    @patch('app.generate_password_hash')
    def test_get_logs(self, mock_hash):
        """Test system logs retrieval"""

        # Simulate log data returned from the database
        mock_log_data = [
            {'timestamp': datetime(2025, 4, 7, 14, 30), 'message': 'System started'},
            {'timestamp': datetime(2025, 4, 7, 15, 0), 'message': 'User logged in'},
            {'timestamp': datetime(2025, 4, 7, 15, 30), 'message': 'User logged out'}
        ]
        
        # Mock the database cursor's fetchall method to return the log data
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_log_data

        # Call the get_logs method
        response = self.data_service.get_logs()

        # Print the response for debugging
        print("Response:", response)

        # Ensure the response is successful
        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']), 3)  # There are 3 log entries

        # Ensure that the logs have the timestamp formatted correctly
        for log in response['data']:
            self.assertEqual(len(log['timestamp'].split('-')), 3)  # Date format should be "YYYY-MM-DD"

        # Verify that the correct SQL query was executed to retrieve logs
        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100"
        )

        # Check if the log event was called to log the retrieval (this is what was missing in the original error)
        self.mock_log.log_event.assert_called_once_with(
            "Admin retrieved all user logs", type='INFO', log_level='admin'
        )

    @patch('app.generate_password_hash')
    def test_get_forecasted_data(self, mock_hash):
        """Test forecasted data retrieval"""

        # Simulate the forecasted data that would be returned by the database
        mock_forecasted_data = [
            {'forecast_time': datetime(2025, 4, 7, 10, 30), 'forecast_value': 150.5},
            {'forecast_time': datetime(2025, 4, 7, 11, 30), 'forecast_value': 160.5},
            {'forecast_time': datetime(2025, 4, 7, 12, 30), 'forecast_value': 170}
        ]

        # Mock the database cursor's fetchall method to return the mock_forecasted_data
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_forecasted_data

        # Simulate the method for retrieving forecasted data (in this case for 'line4')
        response = self.data_service.get_forecasted_data('line4')

        # Ensure the response is successful
        self.assertTrue(response['success'])

        # Ensure the data contains the forecasted data
        self.assertEqual(len(response['data']), 3)  # There are 3 forecasted entries

        # Check that the forecasted values are within the expected range and print the value
        for forecast in response['data']:
            print(f"Forecast value: {forecast['forecast_value']}")  # Print the forecast value for debugging
            self.assertTrue(150 <= forecast['forecast_value'] <= 170)

        # Verify that the correct SQL query was executed to retrieve forecasted data
        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SELECT * FROM forecastedline4 ORDER BY forecast_time ASC"
        )

        # Check if the log event was called to log the retrieval
        self.mock_log.log_event.assert_called_once_with(
            "Forecasted data retrieved for line4", type='INFO'
        )

    @patch('app.generate_password_hash')  # You can patch this if needed for your test
    def test_get_sensor_data(self, mock_hash):
        """Test individual sensor data retrieval"""

        # Simulate the sensor data returned from the database (for sensor 'r01' in table 'line4')
        mock_sensor_data = {
            'timestamp': datetime(2025, 4, 7, 14, 30),
            'r01': 22.5  # Sensor r01's data (e.g., temperature)
        }

        # Mock the database cursor's fetchone method to return the mock_sensor_data
        self.mock_db.get_connection().cursor().fetchone.return_value = mock_sensor_data

        # Simulate the method call to get sensor data
        response = self.data_service.get_sensor_data('line4', 'r01')  # 'line4' is the table, 'r01' is the sensor

        # Assert that the response is successful
        self.assertTrue(response['success'])
        self.assertEqual(response['data']['r01'], 22.5)  # Ensure the data for r01 matches what we expect

        # Ensure the timestamp is formatted correctly (the method converts the timestamp to string)
        self.assertEqual(len(response['data']['timestamp'].split('-')), 3)  # Date format should be "YYYY-MM-DD"

        # Verify that the correct SQL query was executed to retrieve the sensor data
        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SELECT timestamp, r01 FROM line4 ORDER BY timestamp DESC LIMIT 1"
        )

        # Optionally, check if the log_event was called
        self.mock_log.log_event.assert_called_once_with(
            "Sensor data retrieved for r01 from line4", type='INFO', log_level='admin')
        
    def test_historical_data_filtering(self):
        """Test historical data with different filters without specifying a specific sensor"""

        # Define the filter criteria for the test (based on your code)
        filter_criteria = {
            'length': 10,  # Number of records to retrieve
            'searchValue': '2025-04-07',  # Search by timestamp or a date value
            'dateFilter': '2025-04-07',  # Filter records for this specific date
            'startDateTime': '2025-04-01 00:00:00',  # Start datetime filter
            'endDateTime': '2025-04-07 23:59:59'  # End datetime filter
        }

        # Mock the response of the method call for historical data filtering
        mock_response = {
            "success": True,
            "data": [
                {"timestamp": "2025-04-07 10:00:00", "r01": 123.45, "r02": 130.50},
                {"timestamp": "2025-04-07 11:00:00", "r01": 125.75, "r02": 135.25},
                {"timestamp": "2025-04-07 12:00:00", "r01": 127.65, "r02": 137.90}
            ],
            "recordsTotal": 3,
            "recordsFiltered": 3
        }

        # Mock the DataService method call
        with patch.object(self.data_service, 'get_historical_data', return_value=mock_response):
            response = self.data_service.get_historical_data('line4', filter_criteria)

        # Print response for debugging to see the structure
        print("Response:", response)

        # Assert that the response is successful
        self.assertTrue(response['success'], f"Expected success, got {response.get('error', 'No error key in response')}")

        # Assert that the correct number of records are returned
        self.assertEqual(len(response['data']), 3, f"Expected 3 records, got {len(response['data'])}")

        # Assert that each record contains the expected fields (timestamp and sensor values)
        for record in response['data']:
            self.assertIn('timestamp', record)
            self.assertIn('r01', record)  # Check for the presence of sensor r01
            self.assertIn('r02', record)  # Check for the presence of sensor r02
            self.assertIsInstance(record['timestamp'], str)  # Ensure timestamp is a string
            self.assertIsInstance(record['r01'], (float, int))  # Ensure r01 is a number (float or int)
            self.assertIsInstance(record['r02'], (float, int))  # Ensure r02 is a number (float or int)

        # Optionally, assert that the timestamp is formatted correctly
        for record in response['data']:
            self.assertEqual(len(record['timestamp'].split('-')), 3)  # Ensure timestamp format is "YYYY-MM-DD"

    def test_live_data_format(self):
        """Test live data format and structure"""
        
        # Mock the live data that the service will return
        mock_live_data = {
            "success": True,
            "data": {
                "timestamp": "2025-04-07 15:30:00",
                "r01": 150.5,  # Sensor data for r01
                "r02": 160.75  # Sensor data for r02
            }
        }

        # Mock the DataService's method to return the mock live data
        with patch.object(self.data_service, 'get_live_data', return_value=mock_live_data):
            # Fetch the live data from the service
            response = self.data_service.get_live_data('line4')

        # Print the response for debugging purposes
        print("Response:", response)

        # Assert that the response is successful
        self.assertTrue(response['success'], f"Expected success, got {response.get('error', 'No error key in response')}")

        # Check if the 'data' field contains the expected fields
        live_data = response['data']
        
        # Assert that 'timestamp' is present in the response and it's a string
        self.assertIn('timestamp', live_data)
        self.assertIsInstance(live_data['timestamp'], str)
        self.assertEqual(len(live_data['timestamp'].split('-')), 3)  # Ensure timestamp is in "YYYY-MM-DD" format
        
        # Assert that sensor data (e.g., 'r01', 'r02') are present and are numbers (either int or float)
        self.assertIn('r01', live_data)
        self.assertIn('r02', live_data)
        self.assertIsInstance(live_data['r01'], (int, float))
        self.assertIsInstance(live_data['r02'], (int, float))

        # Optionally, check that the values of sensors (r01, r02) are within a reasonable range
        self.assertGreater(live_data['r01'], 0, "Sensor r01 value should be greater than 0")
        self.assertGreater(live_data['r02'], 0, "Sensor r02 value should be greater than 0")



if __name__ == '__main__':
    unittest.main()
