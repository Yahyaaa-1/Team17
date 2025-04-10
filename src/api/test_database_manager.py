import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app import DatabaseManager
from config import Config
from flask import json
import re
from threading import Thread
from werkzeug.security import generate_password_hash

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Set up the database manager and mock configuration"""
        self.db_manager = DatabaseManager()
        self.config_patcher = patch('app.Config', new=Config)
        self.mock_config = self.config_patcher.start()

    def test_get_connection_success(self):
        """Test successful database connection"""
        with patch('mysql.connector.connect') as mock_connect:
            self.db_manager.get_connection()
            mock_connect.assert_called_once_with(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            print("Database connection established successfully.")

    def test_get_connection_failure(self):
        """Test failed database connection"""
        with patch('mysql.connector.connect', side_effect=Exception("Connection failed")):
            conn = self.db_manager.get_connection()
            self.assertIsNone(conn)
            print("Database connection failed as expected.")

    def tearDown(self):
        """Stop the patch for the configuration"""
        self.config_patcher.stop()

if __name__ == '__main__':
    unittest.main()
