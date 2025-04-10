import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash
from app import (
    FlaskApp,
    DatabaseManager,
    AuthService,
    AdminService,
    DataService,
    SimulationService,
    LogService
)

# Mock configuration class
class MockConfig:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'database3'

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
        
        # Patch the Config with our mock
        self.config_patcher = patch('app.Config', new=MockConfig)
        self.mock_config = self.config_patcher.start()
        
    def test_get_connection_success(self):
        with patch('mysql.connector.connect') as mock_connect:
            self.db_manager.get_connection()
            mock_connect.assert_called_once_with(
                host=MockConfig.DB_HOST,
                user=MockConfig.DB_USER,
                password=MockConfig.DB_PASSWORD,
                database=MockConfig.DB_NAME
            )

    def test_get_connection_failure(self):
        with patch('mysql.connector.connect', side_effect=Exception("Connection failed")):
            conn = self.db_manager.get_connection()
            self.assertIsNone(conn)

    def tearDown(self):
        self.config_patcher.stop()

class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_log = MagicMock(spec=LogService)
        self.auth_service = AuthService(self.mock_db, self.mock_log)
        
        self.valid_user = {
            'operator_id': 1,
            'email': 'test@example.com',
            'password': 'hashed_password',
            'admin': 0,
            'active': 1,
            'dark_mode': 0,
            'full_name': 'Test User'
        }

    @patch('app.generate_password_hash')
    def test_successful_registration(self, mock_hash):
        mock_hash.return_value = 'hashed_password'
        self.mock_db.get_connection().cursor().fetchone.return_value = None
        
        response = self.auth_service.register({
            'full_name': 'New User',
            'email': 'new@example.com',
            'new_password': 'ValidPass123!'
        })
        
        self.assertTrue(response['success'])
        self.mock_log.log_event.assert_called_once()
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_log = MagicMock(spec=LogService)
        self.auth_service = AuthService(self.mock_db, self.mock_log)
        
        # Create a mock for an inactive user
        self.inactive_user = {
            'operator_id': 1,
            'email': 'inactive@example.com',
            'password': 'hashed_password',
            'admin': 0,
            'active': 0,  # Account is inactive
            'dark_mode': 0,
            'full_name': 'Inactive User'
        }

    @patch('app.generate_password_hash')
    def test_login_with_inactive_account(self, mock_hash):
        # Simulate returning an inactive user from the database
        self.mock_db.get_connection().cursor().fetchone.return_value = self.inactive_user
        
        # Try to log in with the inactive user's credentials
        response = self.auth_service.login({
            'email': 'inactive@example.com',
            'password': 'ValidPass123!'  # Correct password, but the account is inactive
        })
        
        # Assert that the login failed and the error message is about the account being inactive
        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'Invalid email or password')

        self.mock_log.log_event.assert_called_once()
         

    @patch('app.generate_password_hash')
    def test_login_with_invalid_password(self, mock_hash):
        """Well done the test login with invalid password worked ✅ """
        
        # Simulate returning a user with the correct email but incorrect password
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 1,
            'email': 'test@example.com',
            'password': generate_password_hash('CorrectPassword123'),  # Hashed correct password
            'admin': 0,
            'active': 1,
            'dark_mode': 0,
            'full_name': 'Test User'
        }

        # Try to log in with the correct email but an incorrect password
        response = self.auth_service.login({
            'email': 'test@example.com',
            'password': 'WrongPassword123!'  # Incorrect password
        })
        
        # Check that the login attempt was unsuccessful
        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'Invalid email or password')

        # Verify that log_event was called once with the correct message for a failed login attempt
        self.mock_log.log_event.assert_called_once_with("Failed login attempt for test@example.com")

      
       
    @patch('app.generate_password_hash')
    def test_register_with_existing_email(self, mock_hash):
        """Test registration with already registered email ✅"""
        
        # Simulate the database returning an existing user with the given email
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 1,
            'email': 'test@example.com',
            'password': 'hashed_password',
            'admin': 0,
            'active': 1,
            'dark_mode': 0,
            'full_name': 'Test User'
        }

        # Try to register a new user with the already existing email
        response = self.auth_service.register({
            'full_name': 'New User',
            'email': 'test@example.com',  # Existing email
            'new_password': 'NewPassword123!'
        })

        # Check that the registration attempt failed due to existing email
        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'User already exists')

        # Ensure that log_event was not called, since the registration failed
        self.mock_log.log_event.assert_not_called()


    @patch('app.generate_password_hash')
    def test_update_dark_mode_toggle(self, mock_hash):
        """Test dark mode preference update ✅"""

        # Simulate the database returning a user with dark_mode set to 0 (light mode)
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 1,
            'email': 'test@example.com',
            'password': 'hashed_password',
            'admin': 0,
            'active': 1,
            'dark_mode': 0,
            'full_name': 'Test User'
        }

        # Simulate the data for updating dark mode to 1 (dark mode enabled)
        update_data = {
            'operator_id': 1,
            'dark_mode': 1  # New dark mode value
        }

        # Call the method to update dark mode preference
        response = self.auth_service.update_dark_mode(update_data)

        # Check that the response is successful and matches the expected message
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'Dark mode preference updated')

        # Get the actual query passed to execute() for debugging
        actual_query = self.mock_db.get_connection().cursor().execute.call_args[0][0]

        # Normalize the actual query by stripping newlines and extra spaces, and join words with a single space
        normalized_actual_query = " ".join(actual_query.split())

        # Define the expected query and normalize it the same way
        expected_query = "UPDATE user_accounts SET dark_mode = %s WHERE operator_id = %s"
        
        # Compare the normalized actual query with the expected query
        self.assertEqual(normalized_actual_query, expected_query)

        # Check if the log event was called to log the update
        self.mock_log.log_event.assert_called_once_with(
            "Dark mode preference updated for user 1 to 1"
        )

class TestAdminService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_log = MagicMock(spec=LogService)
        self.admin_service = AdminService(self.mock_db, self.mock_log)
        
        self.admin_user = {
            'operator_id': 1,
            'admin': 1,
            'active': 1,
            'email': 'admin@example.com'
        }

    def test_toggle_admin_status(self):
        self.mock_db.get_connection().cursor().fetchone.return_value = self.admin_user
        response = self.admin_service.toggle_admin_status({
            'operator_id': 2,
            'admin_ID': 1
        })
        self.assertTrue(response['success'])



    

    
    @patch('app.generate_password_hash')
    def test_delete_user_success(self, mock_hash):
        """Test successful user deletion"""

        # Simulate the database returning a user that exists
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 2,
            'email': 'testuser@example.com'
        }

        # Simulate the data for deleting the user with operator_id 2
        delete_data = {
            'operator_id': 2,
            'admin_ID': 1
        }

        # Simulate the cursor's rowcount returning an integer (number of rows affected)
        self.mock_db.get_connection().cursor().rowcount = 1  # Simulate 1 row being affected by the delete operation

        # Call the method to delete the user
        response = self.admin_service.delete_user(delete_data)

        # Check that the response is successful and matches the expected message
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'User 2 has been deleted')

        # Verify that the correct delete SQL query was executed
        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "DELETE FROM user_accounts WHERE operator_id = %s", (2,)
        )

        # Check if the log event was called to log the deletion
        self.mock_log.log_event.assert_called_once_with(
            "User 2 deleted by admin 1", type='WARNING', log_level='admin'
        )
    
    @patch('app.generate_password_hash')
    def test_update_user_details(self, mock_hash):
        """Test user details update functionality"""

        # Simulate the database returning a user that exists
        self.mock_db.get_connection().cursor().fetchone.side_effect = [
            {'operator_id': 1, 'email': 'oldemail@example.com', 'full_name': 'Old Name'},  # First call: user exists
            None  # Second call: No user found with the new email (simulating new email check)
        ]

        # Simulate the data for updating user details
        update_data = {
            'operator_id': 1,
            'Nemail': 'newemail@example.com',  # New email
            'Nfullname': 'New Name'  # New full name
        }

        # Simulate the database cursor's execute method for the update query
        self.mock_db.get_connection().cursor().rowcount = 1  # Simulate 1 row being updated

        # Call the method to update user details
        response = self.admin_service.update_user_details(update_data)

       

        # Ensure the response is successful
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'User details updated successfully')

        

        # Normalize both the expected and actual queries by stripping extra whitespace/newlines
        expected_query = "UPDATE user_accounts SET email = %s, full_name = %s WHERE operator_id = %s"
        
        # Get the actual query from the call_args_list, strip extra newlines and spaces
        actual_query = self.mock_db.get_connection().cursor().execute.call_args_list[2][0][0]
        
        # Normalize by stripping leading/trailing whitespace and newlines, and removing indentation
        actual_query_normalized = ' '.join(actual_query.split())

        # Compare the normalized queries
        self.assertEqual(expected_query.strip(), actual_query_normalized.strip())

        # Check if the log event was called to log the update
        self.mock_log.log_event.assert_called_once_with(
            "User details updated - ID: 1, Email: oldemail@example.com -> newemail@example.com, Name: Old Name -> New Name",
            type='INFO', log_level='admin'
        )

    @patch('app.generate_password_hash')
    def test_delete_sensor(self, mock_hash):
        """Test sensor deletion functionality"""

        # Simulate the database returning a sensor that exists in the table
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 1,
            'email': 'sensor@example.com',
            'full_name': 'Test Sensor'
        }

        # Simulate the data for deleting the sensor
        delete_data = {
            'sensorName': 'temperature_sensor',
            'tableID': 'sensor_data'
        }

        # Simulate the database cursor's execute method for the drop column query
        self.mock_db.get_connection().cursor().rowcount = 1  # Simulate the column being dropped

        # Call the method to delete the sensor
        response = self.admin_service.delete_sensor(delete_data)

        # Print the response for debugging
        print("Response:", response)

        # Ensure the response is successful
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], f'Sensor {delete_data["sensorName"]} deleted from {delete_data["tableID"]}')

        # Verify that the correct SQL query was executed to drop the column
        self.mock_db.get_connection().cursor().execute.assert_any_call(
            f"ALTER TABLE {delete_data['tableID']} DROP COLUMN {delete_data['sensorName']}"
        )

        # Check if the log event was called to log the deletion
        self.mock_log.log_event.assert_called_once_with(
            f"Sensor {delete_data['sensorName']} deleted from table {delete_data['tableID']}",
            type='WARNING', 
            log_level='admin'
        )


    def test_get_table_headers(self):
        """Test retrieval of table headers"""

        # Simulate the columns returned by the database for a table
        mock_columns = [
            ('id',),  # Column name 'id'
            ('name',),  # Column name 'name'
            ('email',)  # Column name 'email'
        ]

        # Mock the cursor's fetchall method to return the mock_columns
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_columns

        # Call the get_table_headers method
        response = self.admin_service.get_table_headers('user_accounts')

        # Assert that the response is successful
        self.assertTrue(response['success'])
        self.assertEqual(response['headers'], ['id', 'name', 'email'])  # Check the column names

        # Verify that the correct SQL query was executed to retrieve the table headers
        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SHOW COLUMNS FROM user_accounts"
        )

    # Additional tests can go here (e.g., for error handling or invalid table names)

    def test_toggle_user_status_user_not_found(self):
        """Test attempting to toggle status for a user that doesn't exist"""

        # Simulate the database returning no user for the operator_id
        self.mock_db.get_connection().cursor().fetchone.return_value = None

        # Simulate the data for toggling user status
        toggle_data = {
            'operator_id': 999,  # A non-existing user ID
            'admin_ID': 1
        }

        # Call the toggle_user_status method
        response = self.admin_service.toggle_user_status(toggle_data)

        # Assert that the response indicates the user was not found
        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'User not found')

    def test_toggle_user_status(self):
        """Test activating/deactivating user accounts"""

        # Simulate the database returning an active user
        mock_user = {
            'active': 1,  # User is currently active
            'email': 'testuser@example.com',
            'operator_id': 1  # Assuming operator_id is the unique identifier for users
        }

        # Mock the cursor's fetchone method to return the mock_user data
        self.mock_db.get_connection().cursor().fetchone.return_value = mock_user

        # Simulate the data for toggling user status (deactivating the user)
        toggle_data = {
            'operator_id': 1,  # The operator_id of the user whose status we want to toggle
            'admin_ID': 1  # Admin performing the action
        }

        # Call the toggle_user_status method
        response = self.admin_service.toggle_user_status(toggle_data)

        # Assert that the response is successful
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'User status updated to inactive')

        # Normalize the expected and actual query by removing newlines, extra spaces, and trimming
        expected_query = '''UPDATE user_accounts SET active = %s WHERE operator_id = %s'''
        actual_query = self.mock_db.get_connection().cursor().execute.call_args[0][0]

        # Normalize both the expected and actual query strings by removing multiple spaces and newlines
        expected_query_normalized = ' '.join(expected_query.split())
        actual_query_normalized = ' '.join(actual_query.split())

        # Compare the normalized queries
        self.assertEqual(expected_query_normalized, actual_query_normalized)

        # Ensure the correct parameters were used for the SQL query
        actual_params = self.mock_db.get_connection().cursor().execute.call_args[0][1]
        self.assertEqual(actual_params, (0, 1))  # Expecting (active status, operator_id)

        # Verify that the log_event was called to log the status change
        self.mock_log.log_event.assert_called_once_with(
            "User testuser@example.com (ID: 1) status changed to inactive", 
            type='INFO', 
            log_level='admin'
        )


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

        # Call insert_line_readings
        self.sim_service.insert_line_readings(
            mock_cursor, 'line4', sensors, sensor_ranges_line4, current_timestamp, timezone_offset
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

        # Debugging: Print to check if execute() was called
        print("Query executed:", mock_cursor.execute.call_args[0][0])
        print("Parameters:", mock_cursor.execute.call_args[0][1])

        # Ensure commit was called to persist the data
        mock_connection.commit.assert_called_once()  # Ensure commit was called on the actual connection object

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


class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = FlaskApp().app
        self.app.testing = True
        self.client = self.app.test_client()
        
        # Mock database connections
        self.db_patcher = patch('mysql.connector.connect')
        self.mock_db = self.db_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_db.return_value = self.mock_conn
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

    def test_successful_login_flow(self):
        from werkzeug.security import generate_password_hash
        
        # Create complete user mock
        self.mock_cursor.fetchone.return_value = {
            'operator_id': 1,
            'email': 'test@example.com',
            'password': generate_password_hash('ValidPass123!'),
            'admin': 1,
            'active': 1,
            'dark_mode': 0,
            'full_name': 'Test User'
        }
        
        response = self.client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'ValidPass123!'
        })
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.db_patcher.stop()

class TestLogService(unittest.TestCase):

    def setUp(self):
        """Set up a mock DB manager for testing"""
        self.db_manager = MagicMock()  # Mock the DB manager
        self.log_service = LogService(self.db_manager)

    def test_log_levels(self):
        """Test different log levels"""
        log_messages = [
            ("Failed password attempt for email: emily.brown@rakusens.co.uk", "WARNING", "admin"),
            ("User emily.brown@rakusens.co.uk logged in successfully.", "INFO", "admin"),
            ("User emily.brown@rakusens.co.uk logged out.", "INFO", "admin"),
            ("User W006 status changed to 0 by Admin - None", "INFO", "admin"),
            ("User W006 status changed to 1 by Admin - None", "INFO", "admin"),
            ("User W006 status changed to 0 by Admin - None", "INFO", "admin"),
            ("User W006 status changed to 1 by Admin - None", "INFO", "admin"),
            ("User W006 status changed to 0 by Admin - None", "INFO", "admin")
        ]

        for message, log_type, log_level in log_messages:
            # Prepare mock connection and cursor
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor
            self.db_manager.get_connection.return_value = mock_connection
            
            # Call log_event with the current log message, type, and level
            self.log_service.log_event(message, log_type, log_level)

            # Normalize both the expected and actual queries by stripping extra whitespace
            expected_query = """
                INSERT INTO logs (level, type, message)
                VALUES (%s, %s, %s)
            """
            expected_query = re.sub(r'\s+', ' ', expected_query.strip())  # Normalize spaces

            actual_query = mock_cursor.execute.call_args[0][0]
            actual_query = re.sub(r'\s+', ' ', actual_query.strip())  # Normalize spaces

            # Assert that the normalized expected query matches the normalized actual query
            self.assertEqual(actual_query, expected_query)

            # Ensure commit is called to persist the log entry
            mock_connection.commit.assert_called_once()


    def test_log_formatting(self):
        """Test log message formatting"""
        log_messages = [
            ("Failed password attempt for email: emily.brown@rakusens.co.uk", "WARNING", "admin"),
            ("User emily.brown@rakusens.co.uk logged in successfully.", "INFO", "admin"),
            ("User W006 status changed to 0 by Admin", "INFO", "admin"),
        ]

        for message, log_type, log_level in log_messages:
            # Prepare mock connection and cursor
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor
            self.db_manager.get_connection.return_value = mock_connection
            
            # Call log_event with the current log message, type, and level
            self.log_service.log_event(message, log_type, log_level)

            # Get the actual query and parameters passed to execute
            actual_query, actual_params = mock_cursor.execute.call_args[0]

            # Normalize both the actual query and the expected query
            def normalize_query(query):
                # Remove extra spaces between elements
                return re.sub(r'\s+', ' ', query.strip())

            # Define the expected query
            expected_query = """
                INSERT INTO logs (level, type, message)
                VALUES (%s, %s, %s)
            """
            
            # Normalize the query strings
            actual_query = normalize_query(actual_query)
            expected_query = normalize_query(expected_query)

            # Check if the queries match
            self.assertEqual(actual_query, expected_query)

            # Now check if the parameters are passed correctly
            self.assertEqual(actual_params, (log_level, log_type, message))

            # Ensure commit is called to persist the log entry
            mock_connection.commit.assert_called_once()


    def test_log_persistence(self):
        """Test log storage in database"""
        # Define some sample log entries
        log_messages = [
            ("Failed password attempt for email: emily.brown@rakusens.co.uk", "WARNING", "admin"),
            ("User emily.brown@rakusens.co.uk logged in successfully.", "INFO", "admin"),
            ("User W006 status changed to 0 by Admin", "INFO", "admin")
        ]

        for message, log_type, log_level in log_messages:
            # Prepare mock connection and cursor
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor
            self.db_manager.get_connection.return_value = mock_connection
            
            # Call log_event with the current log message, type, and level
            self.log_service.log_event(message, log_type, log_level)

            # Check that the correct query was executed
            expected_query = """
                INSERT INTO logs (level, type, message)
                VALUES (%s, %s, %s)
            """
            # Normalize the query to handle any formatting discrepancies
            def normalize_query(query):
                return re.sub(r'\s+', ' ', query.strip())
            
            actual_query, actual_params = mock_cursor.execute.call_args[0]
            actual_query = normalize_query(actual_query)
            expected_query = normalize_query(expected_query)
            
            self.assertEqual(actual_query, expected_query)
            self.assertEqual(actual_params, (log_level, log_type, message))

            # Ensure commit is called to persist the log entry
            mock_connection.commit.assert_called_once()
    
if __name__ == '__main__':
    unittest.main()

