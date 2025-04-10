import unittest
from unittest.mock import MagicMock
from app import AdminService, LogService
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash


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

if __name__ == '__main__':
    unittest.main()
