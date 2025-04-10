import unittest
from unittest.mock import MagicMock
from app import AdminService, LogService
from unittest.mock import patch
from datetime import datetime
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash


class TestAdminService(unittest.TestCase):
    def setUp(self):
        """Set up the necessary mocks and AdminService instance"""
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
        """Test toggling admin status"""
        self.mock_db.get_connection().cursor().fetchone.return_value = self.admin_user
        response = self.admin_service.toggle_admin_status({
            'operator_id': 2,
            'admin_ID': 1
        })
        self.assertTrue(response['success'])

    @patch('app.generate_password_hash')
    def test_delete_user_success(self, mock_hash):
        """Test successful user deletion"""
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 2,
            'email': 'testuser@example.com'
        }

        delete_data = {'operator_id': 2, 'admin_ID': 1}
        self.mock_db.get_connection().cursor().rowcount = 1
        response = self.admin_service.delete_user(delete_data)

        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'User 2 has been deleted')
        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "DELETE FROM user_accounts WHERE operator_id = %s", (2,)
        )
        self.mock_log.log_event.assert_called_once_with(
            "User 2 deleted by admin 1", type='WARNING', log_level='admin'
        )
    
    @patch('app.generate_password_hash')
    def test_update_user_details(self, mock_hash):
        """Test user details update functionality"""
        self.mock_db.get_connection().cursor().fetchone.side_effect = [
            {'operator_id': 1, 'email': 'oldemail@example.com', 'full_name': 'Old Name'},
            None  # Simulating no user with the new email
        ]

        update_data = {'operator_id': 1, 'Nemail': 'newemail@example.com', 'Nfullname': 'New Name'}
        self.mock_db.get_connection().cursor().rowcount = 1
        response = self.admin_service.update_user_details(update_data)

        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'User details updated successfully')

        expected_query = "UPDATE user_accounts SET email = %s, full_name = %s WHERE operator_id = %s"
        actual_query = self.mock_db.get_connection().cursor().execute.call_args_list[2][0][0]
        self.assertEqual(expected_query.strip(), " ".join(actual_query.split()).strip())

        self.mock_log.log_event.assert_called_once_with(
            "User details updated - ID: 1, Email: oldemail@example.com -> newemail@example.com, Name: Old Name -> New Name",
            type='INFO', log_level='admin'
        )

    @patch('app.generate_password_hash')
    def test_delete_sensor(self, mock_hash):
        """Test sensor deletion functionality"""
        self.mock_db.get_connection().cursor().fetchone.return_value = {
            'operator_id': 1,
            'email': 'sensor@example.com',
            'full_name': 'Test Sensor'
        }

        delete_data = {'sensorName': 'temperature_sensor', 'tableID': 'sensor_data'}
        self.mock_db.get_connection().cursor().rowcount = 1
        response = self.admin_service.delete_sensor(delete_data)

        self.assertTrue(response['success'])
        self.assertEqual(response['message'], f'Sensor {delete_data["sensorName"]} deleted from {delete_data["tableID"]}')
        self.mock_db.get_connection().cursor().execute.assert_any_call(
            f"ALTER TABLE {delete_data['tableID']} DROP COLUMN {delete_data['sensorName']}"
        )
        self.mock_log.log_event.assert_called_once_with(
            f"Sensor {delete_data['sensorName']} deleted from table {delete_data['tableID']}",
            type='WARNING', log_level='admin'
        )


    def test_get_table_headers(self):
        """Test retrieval of table headers"""
        mock_columns = [
            ('id',),
            ('name',),
            ('email',)
        ]
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_columns
        response = self.admin_service.get_table_headers('user_accounts')

        self.assertTrue(response['success'])
        self.assertEqual(response['headers'], ['id', 'name', 'email'])

        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SHOW COLUMNS FROM user_accounts"
        )

    def test_toggle_user_status_user_not_found(self):
        """Test attempting to toggle status for a user that doesn't exist"""
        self.mock_db.get_connection().cursor().fetchone.return_value = None
        toggle_data = {'operator_id': 999, 'admin_ID': 1}
        response = self.admin_service.toggle_user_status(toggle_data)

        self.assertFalse(response['success'])
        self.assertEqual(response['error'], 'User not found')

    def test_toggle_user_status(self):
        """Test activating/deactivating user accounts"""
        mock_user = {'active': 1, 'email': 'testuser@example.com', 'operator_id': 1}
        self.mock_db.get_connection().cursor().fetchone.return_value = mock_user

        toggle_data = {'operator_id': 1, 'admin_ID': 1}
        response = self.admin_service.toggle_user_status(toggle_data)

        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'User status updated to inactive')

        expected_query = '''UPDATE user_accounts SET active = %s WHERE operator_id = %s'''
        actual_query = self.mock_db.get_connection().cursor().execute.call_args[0][0]
        self.assertEqual(' '.join(expected_query.split()), ' '.join(actual_query.split()))

        actual_params = self.mock_db.get_connection().cursor().execute.call_args[0][1]
        self.assertEqual(actual_params, (0, 1))

        self.mock_log.log_event.assert_called_once_with(
            "User testuser@example.com (ID: 1) status changed to inactive",
            type='INFO', log_level='admin'
        )


if __name__ == '__main__':
    unittest.main()
