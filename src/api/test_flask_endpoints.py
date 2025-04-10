import unittest
from unittest.mock import MagicMock, patch
from app import FlaskApp
from datetime import datetime
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash

class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        """Set up the Flask app and mock database connections"""
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
        """Test successful login flow with valid credentials"""
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
        """Stop patching the database connection"""
        self.db_patcher.stop()

if __name__ == '__main__':
    unittest.main()
