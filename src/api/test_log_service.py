import unittest
from unittest.mock import MagicMock, patch
from app import LogService
import re
from datetime import datetime
from flask import json
from threading import Thread 
from werkzeug.security import generate_password_hash

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

        print("Test log levels passed successfully.")

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

        print("Test log formatting passed successfully.")

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

        print("Test log persistence passed successfully.")

if __name__ == '__main__':
    unittest.main()
