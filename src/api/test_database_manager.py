import unittest
from unittest.mock import patch, MagicMock
from app import DatabaseManager
from config import Config
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
        self.config_patcher = patch('app.Config', new=Config)
        self.mock_config = self.config_patcher.start()

    def test_get_connection_success(self):
        with patch('mysql.connector.connect') as mock_connect:
            self.db_manager.get_connection()
            mock_connect.assert_called_once_with(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )

    def test_get_connection_failure(self):
        with patch('mysql.connector.connect', side_effect=Exception("Connection failed")):
            conn = self.db_manager.get_connection()
            self.assertIsNone(conn)

    def tearDown(self):
        self.config_patcher.stop()

if __name__ == '__main__':
    unittest.main()
