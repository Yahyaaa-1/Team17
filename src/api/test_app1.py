import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
from flask import json
from RefactoredApp import (
    FlaskApp,
    DatabaseManager,
    AuthService,
    AdminService,
    DataService,
    SimulationService,
    LogService
)

# Add this mock configuration class
class MockConfig:
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'rakusensdatabase'

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
        
        # Patch the Config with our mock
        self.config_patcher = patch('RefactoredApp.Config', new=MockConfig)
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

    @patch('RefactoredApp.generate_password_hash')
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

if __name__ == '__main__':
    unittest.main()


# AuthService Tests
def test_login_with_inactive_account(self):
    """Test login attempt with a deactivated account"""

def test_login_with_invalid_password(self):
    """Test login attempt with wrong password"""

def test_register_with_existing_email(self):
    """Test registration with already registered email"""

def test_update_dark_mode_toggle(self):
    """Test dark mode preference update"""

# AdminService Tests
def test_delete_user_success(self):
    """Test successful user deletion"""

def test_update_user_details(self):
    """Test user details update functionality"""

def test_get_table_headers(self):
    """Test retrieval of table headers"""

def test_toggle_user_status(self):
    """Test activating/deactivating user accounts"""

def test_delete_sensor(self):
    """Test sensor deletion functionality"""

# DataService Tests
def test_get_logs(self):
    """Test system logs retrieval"""

def test_get_forecasted_data(self):
    """Test forecasted data retrieval"""

def test_get_sensor_data(self):
    """Test individual sensor data retrieval"""

def test_historical_data_filtering(self):
    """Test historical data with different filters"""

def test_live_data_format(self):
    """Test live data format and structure"""

# SimulationService Tests
def test_timezone_offset(self):
    """Test timezone offset calculation"""

def test_multiple_sensor_readings(self):
    """Test generation of multiple sensor readings"""

def test_simulation_start_stop(self):
    """Test simulation thread management"""

def test_insert_line_readings(self):
    """Test database insertion of readings"""

def test_reading_range_validation(self):
    """Test sensor readings stay within defined ranges"""


# Database Manager Tests
def test_connection_pooling(self):
    """Test database connection pooling"""

def test_connection_timeout(self):
    """Test connection timeout handling"""

def test_connection_retry(self):
    """Test connection retry mechanism"""

def test_transaction_rollback(self):
    """Test transaction rollback on error"""

def test_connection_cleanup(self):
    """Test proper connection cleanup"""

# LogService Tests
def test_log_levels(self):
    """Test different log levels"""

def test_log_formatting(self):
    """Test log message formatting"""

def test_log_persistence(self):
    """Test log storage in database"""

def test_log_retrieval(self):
    """Test log retrieval functionality"""

def test_error_logging(self):
    """Test error logging mechanism"""

# Edge Cases and Error Handling Tests

def test_invalid_data_formats(self):
    """Test handling of invalid data formats"""

