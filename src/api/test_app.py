import unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash, check_password_hash
from Capp import app  # Import your Flask app

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        # Set up the test client and any necessary configurations
        self.app = app.test_client()
        self.app.testing = True

    # Tests for the registration endpoint
    def test_register_success(self):
        # Test successful registration
        response = self.app.post('/api/register', json={
            'email': 'test@example.com',
            'temp_password': 'temp123',
            'new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

    def test_register_missing_fields(self):
        # Test registration with missing fields
        response = self.app.post('/api/register', json={
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing required fields', response.data)

    def test_register_invalid_credentials(self):
        # Test registration with invalid temporary password
        response = self.app.post('/api/register', json={
            'email': 'test@example.com',
            'temp_password': 'wrongtemp',
            'new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid credentials', response.data)

    def test_register_user_already_exists(self):
        # Test registration when user already exists
        response = self.app.post('/api/register', json={
            'email': 'existing_user@example.com',
            'temp_password': 'temp123',
            'new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'User already registered', response.data)

    # Tests for the login endpoint
    def test_login_success(self):
        # Test successful login
        response = self.app.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful', response.data)

    def test_login_missing_fields(self):
        # Test login with missing fields
        response = self.app.post('/api/login', json={
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing required fields', response.data)

    def test_login_invalid_email(self):
        # Test login with invalid email
        response = self.app.post('/api/login', json={
            'email': 'invalid@example.com',
            'password': 'somepassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid email', response.data)

    def test_login_invalid_password(self):
        # Test login with incorrect password
        response = self.app.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid password', response.data)

    def test_login_inactive_user(self):
        # Test login for an inactive user
        response = self.app.post('/api/login', json={
            'email': 'inactive_user@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Account not yet approved', response.data)

    # Tests for the update dark mode endpoint
    def test_update_dark_mode_success(self):
        # Test updating dark mode preference successfully
        response = self.app.post('/api/update-dark-mode', json={
            'operator_id': '123',
            'dark_mode': 'enabled'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dark mode preference updated', response.data)

    def test_update_dark_mode_missing_operator_id(self):
        # Test updating dark mode with missing operator ID
        response = self.app.post('/api/update-dark-mode', json={
            'dark_mode': 'enabled'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Missing operator ID', response.data)

    def test_update_dark_mode_no_data_received(self):
        # Test updating dark mode with no data received
        response = self.app.post('/api/update-dark-mode', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No data received', response.data)

    def test_update_dark_mode_database_failure(self):
        # Simulate a database failure (mocking can be used here)
        # This would require a more complex setup with mocking libraries
        response = self.app.post('/api/update-dark-mode', json={
            'operator_id': '123',
            'dark_mode': 'enabled'
        })
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Database connection failed', response.data)

    @patch('Capp.get_db_connection')  # Mock the database connection
    def test_register_success(self, mock_get_db_connection):
        # Mock the database response for employee verification
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = {
            'operator_id': 'W001',
            'email': 'john.doe@rakusens.co.uk',
            'full_name': 'John Doe',
            'temp_password': 'TempPass123!'
        }

        response = self.app.post('/api/register', json={
            'email': 'john.doe@rakusens.co.uk',
            'temp_password': 'TempPass123!',
            'new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

    @patch('Capp.get_db_connection')
    def test_register_invalid_temp_password(self, mock_get_db_connection):
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = {
            'operator_id': 'W001',
            'email': 'john.doe@rakusens.co.uk',
            'full_name': 'John Doe',
            'temp_password': 'WrongTempPass!'
        }

        response = self.app.post('/api/register', json={
            'email': 'john.doe@rakusens.co.uk',
            'temp_password': 'TempPass123!',
            'new_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid credentials', response.data)

    @patch('Capp.get_db_connection')
    def test_login_success(self, mock_get_db_connection):
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = {
            'operator_id': 'W001',
            'email': 'john.doe@rakusens.co.uk',
            'full_name': 'John Doe',
            'password': generate_password_hash('newpassword123'),  # Use the hashed password
            'admin': 0,
            'active': 1,
            'dark_mode': 0
        }

        response = self.app.post('/api/login', json={
            'email': 'john.doe@rakusens.co.uk',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful', response.data)

    @patch('Capp.get_db_connection')
    def test_login_invalid_email(self, mock_get_db_connection):
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = None  # Simulate non-existent user

        response = self.app.post('/api/login', json={
            'email': 'invalid@example.com',
            'password': 'somepassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid email', response.data)


    # Add more tests as needed...

if __name__ == '__main__':
    unittest.main()