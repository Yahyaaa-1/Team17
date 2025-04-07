import unittest
from unittest.mock import patch, MagicMock
from RefactoredApp import FlaskApp, DatabaseManager, SimulationService, AuthService, AdminService, DataService
from flask import json
from datetime import datetime,timedelta

class TestFlaskApp(unittest.TestCase):


    @classmethod
    def setUp(self):
        # Setup that runs before all test #
        self.app = FlaskApp().app
        self.app.testing = True
        self.client = self.app.test_client()
        
        # Mock database connections before all tests
        self.db_patcher = patch('mysql.connector.connect')
        self.mock_db = self.db_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_db.return_value = self.mock_conn
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

    def tearDown(self):
        self.db_patcher.stop()

    # Helper methods
    def mock_db_execute(self, return_value=None):
        self.mock_cursor.fetchone.return_value = return_value
        self.mock_cursor.fetchall.return_value = return_value or []
        return self.mock_cursor

    # Auth Service Tests
    def test_register_success(self):
        self.mock_db_execute(None)  # No existing user
        response = self.client.post('/api/register', json={
            'full_name': 'Test User',
            'email': 'test@example.com',
            'new_password': 'Test1234!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

    def test_register_missing_fields(self):
        response = self.client.post('/api/register', json={
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing fields', response.data)

    def test_login_success(self):
        from werkzeug.security import generate_password_hash
        hashed_pw = generate_password_hash('Test1234!')
        # Add all required user fields from your User model
        self.mock_db_execute({
            'operator_id': 1,
            'email': 'test@example.com', 
            'password': hashed_pw,
            'admin': 0,
            'active': 1,
            'dark_mode': 0,
            'full_name': 'Test User'
        })
        
        response = self.client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'Test1234!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful', response.data)

    # Admin Service Tests
    def test_get_user_accounts(self):
        mock_data = [{
            'operator_id': 1,
            'email': 'admin@example.com',
            'full_name': 'Admin User',
            'admin': 1,
            'active': 1,
            'dark_mode': 0
        }]
        
        
        self.mock_cursor.fetchall.return_value = mock_data
        response = self.client.get('/api/admin/user-accounts')
        self.assertEqual(response.status_code, 200)

    def test_toggle_admin_status(self):
        self.mock_db_execute({'admin': 0})
        response = self.client.post('/api/admin/toggle-admin-status', json={
            'operator_id': 1,
            'admin_ID': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'admin status updated', response.data)

    # Data Service Tests
    @patch('RefactoredApp.DataService.get_historical_data')
    def test_get_historical_data(self, mock_get):
        mock_get.return_value = {'success': True, 'data': []}
        response = self.client.post('/api/historical-data/line4', json={})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data', response.data)

    # Error Handling Tests
    def test_database_connection_failure(self):
        self.mock_db.return_value = None  # Simulate DB connection failure
        response = self.client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'Test1234!'
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Database connection failed', response.data)

    # Simulation Service Tests
    @patch('RefactoredApp.render_template')
    def test_simulation_start(self, mock_render):
        mock_render.return_value = "Mocked Home Page"
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_with('home.html')

    # Edge Cases
    def test_invalid_route(self):
        response = self.client.get('/invalid-route')
        self.assertEqual(response.status_code, 404)

    def test_update_password_short(self):
        response = self.client.post('/api/update-password', json={
            'operator_id': 1,
            'new_password': 'short'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'at least 8 characters', response.data)

if __name__ == '__main__':
    unittest.main()