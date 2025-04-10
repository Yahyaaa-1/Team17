import unittest
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash
from app import AuthService, LogService
from datetime import datetime
from flask import json
import re
from threading import Thread


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
        """Test login with invalid password"""
        
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
        self.mock_log.log_event.assert_called_once_with("Failed login attempt for test@example.com")

    @patch('app.generate_password_hash')
    def test_register_with_existing_email(self, mock_hash):
        """Test registration with already registered email"""
        
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
        self.mock_log.log_event.assert_not_called()

    @patch('app.generate_password_hash')
    def test_update_dark_mode_toggle(self, mock_hash):
        """Test dark mode preference update"""

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

        # Get the actual query passed to execute()
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


if __name__ == '__main__':
    unittest.main()
