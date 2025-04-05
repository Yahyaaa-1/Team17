from flask import Flask, jsonify, request
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Database Connection Class
class Database:
    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(
                host='localhost',  # Your database host
                user='root',       # Your database user
                password='',       # Your database password
                database='test_db' # Your database name
            )
            return connection
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return None

# User Model Class (Handles database queries related to user)
class UserModel:
    @staticmethod
    def get_user_by_email(email):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user

    @staticmethod
    def create_user(email, full_name, password):
        connection = Database.get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO user_accounts (email, full_name, password, admin, active, dark_mode) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email, full_name, password, 0, 0, 0))
        connection.commit()
        cursor.close()
        connection.close()

# AuthService Class (Handles business logic like user registration and login)
class AuthService:
    def register_user(self, full_name, email, password):
        # Hash password before saving it
        hashed_password = generate_password_hash(password)
        # Create user in database
        UserModel.create_user(email, full_name, hashed_password)

    def login_user(self, email, password):
        user = UserModel.get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            return True  # User authenticated
        return False  # Authentication failed

# Admin Service Class (Handles admin-specific logic like user management)
class AdminService:
    @staticmethod
    def get_all_users():
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts")
        users = cursor.fetchall()
        cursor.close()
        connection.close()
        return users

    @staticmethod
    def toggle_user_admin_status(operator_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT admin FROM user_accounts WHERE operator_id = %s", (operator_id,))
        user = cursor.fetchone()
        if user:
            new_status = 0 if user['admin'] == 1 else 1
            cursor.execute("UPDATE user_accounts SET admin = %s WHERE operator_id = %s", (new_status, operator_id))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        return False

# Logging Service Class (Handles log functionality)
class LoggingService:
    @staticmethod
    def create_log(level, type, message):
        connection = Database.get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO logs (level, type, message) 
            VALUES (%s, %s, %s)
        """, (level, type, message))
        connection.commit()
        cursor.close()
        connection.close()

# AuthController (Handles Registration and Login Routes)
class AuthController:
    def __init__(self):
        self.auth_service = AuthService()

    def register(self):
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('new_password')

        if not all([full_name, email, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        try:
            self.auth_service.register_user(full_name, email, password)
            return jsonify({'success': True, 'message': 'Registration successful'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    def login(self):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if self.auth_service.login_user(email, password):
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

# AdminController (Handles Admin Routes)
class AdminController:
    def __init__(self):
        self.admin_service = AdminService()

    def get_users(self):
        # Handle getting all user accounts
        users = self.admin_service.get_all_users()
        return jsonify({'users': users})

    def post(self):
        # Handle toggling user admin status
        data = request.get_json()
        operator_id = data.get('operator_id')
        if operator_id:
            success = self.admin_service.toggle_user_admin_status(operator_id)
            if success:
                return jsonify({'success': True, 'message': 'User admin status updated'})
            return jsonify({'success': False, 'error': 'User not found'}), 404
        return jsonify({'success': False, 'error': 'Missing operator_id'}), 400

# LoggingController (Handles Log Routes)
class LoggingController:
    def __init__(self):
        self.logging_service = LoggingService()

    def post(self):
        # Handle creating a log
        data = request.get_json()
        level = data.get('level', 'INFO')
        type = data.get('type', 'General')
        message = data.get('message')
        
        if message:
            self.logging_service.create_log(level, type, message)
            return jsonify({'success': True, 'message': 'Log event triggered'})
        return jsonify({'success': False, 'error': 'Missing log message'}), 400

# SensorController (Handles Sensor Data Routes)
class SensorController:
    @staticmethod
    def get_live_data(line):
        try:
            connection = Database.get_connection()
            cursor = connection.cursor(dictionary=True)
            valid_lines = ["line4", "line5"]
            if line not in valid_lines:
                return jsonify({'error': 'Invalid line selected'}), 400

            query = f"SELECT * FROM {line} ORDER BY timestamp DESC LIMIT 1"
            cursor.execute(query)
            data = cursor.fetchone()

            if not data:
                return jsonify({'error': 'No live data available'}), 404

            data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({'success': True, 'data': data}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection:
                connection.close()

    @staticmethod
    def get_sensor_data(line, sensor):
        try:
            connection = Database.get_connection()
            cursor = connection.cursor(dictionary=True)
            valid_lines = ["line4", "line5"]
            if line not in valid_lines:
                return jsonify({'error': 'Invalid line selected'}), 400

            query = f"SELECT timestamp, {sensor} FROM {line} ORDER BY timestamp DESC LIMIT 1"
            cursor.execute(query)
            data = cursor.fetchone()

            if not data:
                return jsonify({'error': 'No data available for this sensor'}), 404

            data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({'success': True, 'data': data}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if connection:
                connection.close()

# Registering Controllers as Routes
app.add_url_rule('/api/auth', view_func=AuthController().register)
app.add_url_rule('/api/login', view_func=AuthController().login)
app.add_url_rule('/api/admin/user-accounts', view_func=AdminController().get_users)
app.add_url_rule('/api/admin/toggle-user-admin', view_func=AdminController().post)
app.add_url_rule('/api/log', view_func=LoggingController().post)
app.add_url_rule('/api/live-data/<line>', view_func=SensorController.get_live_data)
app.add_url_rule('/api/sensor-data/<line>/<sensor>', view_func=SensorController.get_sensor_data)

if __name__ == '__main__':
    app.run(debug=True)
