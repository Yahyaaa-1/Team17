from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash
from flask_cors import CORS
import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
import logging
import random
from datetime import datetime

app = Flask(__name__)

# CORS configuration
CORS(app, resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return connection
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        return None

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Log event
def log_event(message, type='INFO', log_level='admin'):
    """
    Logs an event to the database with the specified message, type, and log level.
    """
    try:
        # Establish a database connection
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Insert the log entry into the logs table
            cursor.execute("""
                INSERT INTO logs (level, type, message) 
                VALUES (%s, %s, %s)
            """, (log_level, type, message))
            
            connection.commit()
            cursor.close()
            connection.close()
    except Exception as e:
        # Log an error if the logging operation fails
        logging.error(f"Failed to log event: {e}")

# Routes
# Trigger a log event
@app.route('/api/log', methods=['POST', 'OPTIONS'])
def trigger_log():
    """
    API endpoint to trigger a log event. Accepts POST requests with log details.
    """
    if request.method == "OPTIONS":
        # Handle preflight OPTIONS request for CORS
        return jsonify({"success": True})
    
    try:
        # Parse JSON data from the request
        data = request.get_json()
        message = data.get('message')
        type = data.get('type', 'INFO')  # Default log type is 'INFO'
        log_level = data.get('level', 'admin')  # Default log level is 'admin'
        
        # Log the event using the log_event function
        log_event(message, type=type, log_level=log_level)
        
        # Return success response
        return jsonify({'success': True, 'message': 'Log event triggered'})
    except Exception as e:
        # Log an error if the logging operation fails
        logging.error(f"Logging error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Verify employee credentials
@app.route('/api/verify-employee', methods=['POST', 'OPTIONS'])
def verify_employee():
    """
    API endpoint to verify employee credentials. Accepts POST requests with email and temporary password.
    """
    if request.method == "OPTIONS":
        # Handle preflight OPTIONS request for CORS
        return jsonify({"success": True})

    try:
        # Parse JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        email = data.get('email')
        temp_password = data.get('temp_password')

        # Check for missing credentials
        if not email or not temp_password:
            return jsonify({'success': False, 'error': 'Missing credentials'}), 400

        # Establish a database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        
        # Query to verify employee credentials
        cursor.execute("""
            SELECT * FROM employee_registry 
            WHERE email = %s AND temp_password = %s
        """, (email, temp_password))
        
        employee = cursor.fetchone()
        cursor.close()
        connection.close()

        # Check if employee exists
        if employee:
            return jsonify({'success': True, 'message': 'Verification successful'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    except Exception as e:
        # Log an error if the verification process fails
        logging.error(f"Error in verify_employee: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Register a new user
@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    """
    API endpoint to register a new user. Accepts POST requests with email, temporary password, and new password.
    """
    if request.method == "OPTIONS":
        # Handle preflight OPTIONS request for CORS
        return jsonify({"success": True})
    
    try:
        # Parse JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        email = data.get('email')
        temp_password = data.get('temp_password')
        new_password = data.get('new_password')

        # Check for missing required fields
        if not all([email, temp_password, new_password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Establish a database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        
        # Verify employee credentials
        cursor.execute("""
            SELECT * FROM employee_registry 
            WHERE email = %s AND temp_password = %s
        """, (email, temp_password))
        
        employee = cursor.fetchone()

        if not employee:
            cursor.close()
            connection.close()
            log_event(f"Registration failed for {email}: Invalid Credentials", type='WARNING', log_level='admin')
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

        # Check if user already exists
        cursor.execute("""
            SELECT * FROM user_accounts 
            WHERE email = %s
        """, (email,))
        
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': 'User already registered'}), 400

        # Hash the new password and insert new user into the database
        hashed_password = generate_password_hash(new_password)
        cursor.execute("""
            INSERT INTO user_accounts 
            (operator_id, email, full_name, password, admin, active, dark_mode) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (employee['operator_id'], email, employee['full_name'], hashed_password, 0, 0, 0))

        connection.commit()
        cursor.close()
        connection.close()

        # Log the successful registration
        log_event(f"New user registered: {email}", type='INFO', log_level='admin')
        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        # Log an error if the registration process fails
        logging.error(f"Error in registration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# Endpoint to log in a user
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    """
    API endpoint to log in a user. Accepts POST requests with email and password.
    """
    if request.method == "OPTIONS":
        # Handle preflight OPTIONS request for CORS
        return jsonify({"success": True})

    try:
        # Parse JSON data from the request
        data = request.get_json()
        if not data:
            log_event("Login attempt with no data", type='WARNING', log_level='admin')
            return jsonify({'success': False, 'error': 'No data received'}), 400

        email = data.get('email')
        password = data.get('password')

        # Check for missing credentials
        if not all([email, password]):
            log_event(f"Login attempt with missing credentials. Email: {email}", type='WARNING', log_level='admin')
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Establish a database connection
        connection = get_db_connection()
        if not connection:
            log_event("Database connection failed during login", type='ERROR', log_level='admin')
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        
        # Query to fetch user details based on email
        cursor.execute("""
            SELECT operator_id, email, full_name, password, admin, active, dark_mode 
            FROM user_accounts 
            WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        # Check if user exists
        if not user:
            log_event(f"Login attempt for non-existent email: {email}", type='WARNING', log_level='admin')
            return jsonify({'success': False, 'error': 'Invalid email'}), 401

        # Verify the password
        if not check_password_hash(user['password'], password):
            log_event(f"Failed password attempt for email: {email}", type='WARNING', log_level='admin')
            return jsonify({'success': False, 'error': 'Invalid password'}), 401

        # Check if the user account is active
        if not user['active']:
            log_event(f"Login attempt for inactive user: {email}", type='INFO', log_level='admin')
            return jsonify({'success': False, 'error': 'Account not yet approved. Please contact administrator.', 'active': False}), 403

        # Log successful login
        log_event(f"User {email} logged in successfully", type='INFO', log_level='admin')
        return jsonify({
            'success': True, 
            'message': 'Login successful',
            'active': True,
            'operator_id': user['operator_id'],
            'email': user['email'],
            'full_name': user['full_name'],
            'dark_mode': user['dark_mode'],
            'is_admin': user['admin']
        })

    except Exception as e:
        # Log any unexpected errors during the login process
        logging.error(f"Unexpected error during login: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500
    
# Update the dark mode preference for a user
@app.route('/api/update-dark-mode', methods=['POST', 'OPTIONS'])
def update_dark_mode():
    """
    API endpoint to update the dark mode preference for a user. Accepts POST requests with operator ID and dark mode status.
    """
    if request.method == "OPTIONS":
        # Handle preflight OPTIONS request for CORS
        return jsonify({"success": True})

    try:
        # Parse JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        operator_id = data.get('operator_id')
        dark_mode = data.get('dark_mode', 'disabled')  # Default to 'disabled' if not provided

        # Check for missing operator ID
        if not operator_id:
            return jsonify({'success': False, 'error': 'Missing operator ID'}), 400

        # Establish a database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor()
        
        # Update the dark mode preference in the database
        cursor.execute("""
            UPDATE user_accounts
            SET dark_mode = %s
            WHERE operator_id = %s
        """, (dark_mode, operator_id))

        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()

        # Return success response
        return jsonify({'success': True, 'message': 'Dark mode preference updated'})

    except Exception as e:
        # Log any errors that occur during the update process
        logging.error(f"Error updating dark mode: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Admin Routes
# Get all user accounts
@app.route('/api/admin/user-accounts', methods=['GET', 'OPTIONS'])
def get_user_accounts():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts")
        user_accounts = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'message': 'Retrieved user accounts successfully',
            'user_accounts': user_accounts
        })

    except Exception as e:
        logging.error(f"Error retrieving user accounts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# Get all employees
@app.route('/api/admin/employee-reg', methods=['GET', 'OPTIONS'])
def get_employee_reg():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employee_registry")
        employee_registry = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'message': 'Retrieved employee registry successfully',
            'employee_registry': employee_registry
        })

    except Exception as e:
        logging.error(f"Error retrieving employee registry: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# Toggle user admin status
@app.route('/api/admin/toggle-admin-status', methods=['POST', 'OPTIONS'])
def toggle_user_admin():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')

        if not operator_id:
            return jsonify({'success': False, 'error': 'Missing Operator ID'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT admin FROM user_accounts WHERE operator_id = %s", (operator_id,))
        user = cursor.fetchone()

        if user:
            current_status = int(user['admin'])
            new_status = 1 if current_status == 0 else 0

            cursor.execute("UPDATE user_accounts SET admin = %s WHERE operator_id = %s", (new_status, operator_id))
            connection.commit()

            log_event(f"User {operator_id} status changed to {new_status} by Admin - {admin_ID}", type='INFO', log_level='admin')
            return jsonify({
                'success': True,
                'message': f'User status updated to {"admin" if new_status == 1 else "not admin"}',
                'new_status': new_status
            })

        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error toggling user admin status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Toggle user status
@app.route('/api/admin/toggle-user-status', methods=['POST', 'OPTIONS'])
def toggle_user_status():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        operator_id = data.get('operator_id')

        if not operator_id:
            return jsonify({'success': False, 'error': 'Missing Operator ID'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT active FROM user_accounts WHERE operator_id = %s", (operator_id,))
        user = cursor.fetchone()

        if user:
            current_status = int(user['active'])
            new_status = 1 if current_status == 0 else 0

            cursor.execute("UPDATE user_accounts SET active = %s WHERE operator_id = %s", (new_status, operator_id))
            connection.commit()

            return jsonify({
                'success': True,
                'message': f'User status updated to {"active" if new_status == 1 else "inactive"}',
                'new_status': new_status
            })

        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error toggling user status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Delete user account
@app.route('/api/admin/delete-user', methods=['POST', 'OPTIONS'])
def delete_user():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')

        if not operator_id:
            return jsonify({'success': False, 'error': 'Missing Operator ID'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts WHERE operator_id = %s", (operator_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute("DELETE FROM user_accounts WHERE operator_id = %s", (operator_id,))
            affected_rows = cursor.rowcount
            connection.commit()

            if affected_rows > 0:
                log_event(f"User {operator_id} deleted by admin - {admin_ID}", type='WARNING', log_level='admin')
                return jsonify({'success': True, 'message': f'User {operator_id} has been deleted', 'rows_affected': affected_rows})
            else:
                return jsonify({'success': False, 'message': f'Delete operation failed for user {operator_id}', 'rows_affected': affected_rows}), 500

        else:
            return jsonify({'success': False, 'message': f'User {operator_id} not found'}), 404

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500
    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Delete employee
@app.route('/api/admin/delete-employee', methods=['POST', 'OPTIONS'])
def delete_employee():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')

        if not operator_id:
            return jsonify({'success': False, 'error': 'Missing Operator ID'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employee_registry WHERE operator_id = %s", (operator_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute("DELETE FROM employee_registry WHERE operator_id = %s", (operator_id,))
            employee = cursor.rowcount
            connection.commit()

            if employee > 0:
                log_event(f"Employee Reg {operator_id} deleted by admin - {admin_ID}", type='WARNING', log_level='admin')
                return jsonify({'success': True, 'message': f'User {operator_id} has been deleted', 'employee_rows_affected': employee})
            else:
                return jsonify({'success': False, 'message': f'Delete operation failed for user {operator_id}'}), 500

        else:
            return jsonify({'success': False, 'message': f'User {operator_id} not found'}), 404

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500
    except Exception as e:
        logging.error(f"Error deleting employee: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Update User details
@app.route('/api/admin/update-user-details', methods=['POST', 'OPTIONS'])
def update_user_details():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        operator_id = data.get('operator_id')
        email = data.get('Nemail')
        password = data.get('NtempPass')
        fullname = data.get('Nfullname')

        if not all([operator_id, email, password, fullname]):
            missing_fields = [field for field in ['Operator ID', 'Email', 'Password', 'Fullname'] if not data.get(field.lower().replace(' ', '_'))]
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employee_registry WHERE operator_id = %s", (operator_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute("""
                UPDATE employee_registry
                SET email = %s, full_name = %s, temp_password = %s
                WHERE operator_id = %s
            """, (email, fullname, password, operator_id))
            connection.commit()

            return jsonify({'success': True, 'message': 'User details updated'})

        else:
            return jsonify({'success': False, 'error': 'User does not exist'}), 404

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'success': False, 'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error updating user details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


# Delete sensor
@app.route('/api/admin/delete-sensor', methods=['POST', 'OPTIONS'])
def deleteSensor():
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        sensor = data.get('sensorName')
        tableID = data.get('tableID')
       

        if not [sensor]:
            return jsonify({'success': False, 'error': 'Missing Sensor Name'}), 400
        
        if not [tableID]:
            return jsonify({'success': False, 'error': 'Missing Table id'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = connection.cursor(dictionary=True)

             # Check if the column exists using SHOW COLUMNS
            cursor.execute(f"SHOW COLUMNS FROM {tableID} LIKE %s", (sensor,))
            column_exists = cursor.fetchone()
            
            if not column_exists:
                cursor.close()
                connection.close()
                return jsonify({'success': False, 'error': f'Sensor {sensor} does not exist in the table'}), 400

           # Delete the sensor column
            cursor.execute(f"ALTER TABLE {tableID} DROP COLUMN {sensor}")
            connection.commit()
            
            cursor.close()
            connection.close()
            return jsonify({'success': True, 'message': f'Sensor {sensor} deleted from {tableID}'})

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'success': False, 'error': str(err)}), 500
        finally:
            cursor.close()
            connection.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    
# Sensor simulation
LINE_4_SENSORS = ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"]
LINE_5_SENSORS = ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"]

SENSOR_RANGES_LINE4 = {
    "r01": {"avg": 129.10, "min": 16.00, "max": 258.00},
    "r02": {"avg": 264.81, "min": 18.00, "max": 526.00},
    "r03": {"avg": 255.77, "min": 17.00, "max": 476.00},
    "r04": {"avg": 309.04, "min": 13.00, "max": 554.00},
    "r05": {"avg": 253.94, "min": 10.00, "max": 440.00},
    "r06": {"avg": 268.39, "min": 8.00, "max": 485.00},
    "r07": {"avg": 263.18, "min": 9.00, "max": 525.00},
    "r08": {"avg": 210.97, "min": 8.00, "max": 434.00}
}

SENSOR_RANGES_LINE5 = {
    "r01": {"avg": 133.31, "min": 18.00, "max": 226.00},
    "r02": {"avg": 203.01, "min": 18.00, "max": 308.00},
    "r03": {"avg": 164.63, "min": 16.00, "max": 262.00},
    "r04": {"avg": 223.17, "min": 17.00, "max": 354.00},
    "r05": {"avg": 183.02, "min": 16.00, "max": 278.00},
    "r06": {"avg": 280.04, "min": 16.00, "max": 430.00},
    "r07": {"avg": 277.71, "min": 17.00, "max": 415.00},
    "r08": {"avg": 229.20, "min": 16.00, "max": 364.00},
    "r09": {"avg": 227.06, "min": 16.00, "max": 307.00},
    "r10": {"avg": 321.24, "min": 15.00, "max": 489.00},
    "r11": {"avg": 225.51, "min": 14.00, "max": 357.00},
    "r12": {"avg": 297.59, "min": 15.00, "max": 403.00},
    "r13": {"avg": 238.31, "min": 16.00, "max": 330.00},
    "r14": {"avg": 284.27, "min": 15.00, "max": 421.00},
    "r15": {"avg": 174.30, "min": 15.00, "max": 255.00},
    "r16": {"avg": 220.43, "min": 13.00, "max": 365.00},
    "r17": {"avg": 151.66, "min": 0.00, "max": 241.00}
}

sensor_temps = {sensor: SENSOR_RANGES_LINE4[sensor]["avg"] for sensor in LINE_4_SENSORS}
sensor_temps.update({sensor: SENSOR_RANGES_LINE5[sensor]["avg"] for sensor in LINE_5_SENSORS})

def generate_temperature_readings():
    while True:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            current_timestamp = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

            def get_timezone_offset():
                current_month = time.localtime().tm_mon
                return "+01" if 4 <= current_month <= 10 else "+00"

            timezone_offset = get_timezone_offset()

            line4_values = [current_timestamp, timezone_offset]
            for sensor in LINE_4_SENSORS:
                temp = sensor_temps[sensor]
                limits = SENSOR_RANGES_LINE4[sensor]
                delta = random.uniform(-0.2, 0.2)
                new_temp = max(limits["min"], min(limits["max"], temp + delta))
                sensor_temps[sensor] = round(new_temp, 2)
                line4_values.append(sensor_temps[sensor])

            cursor.execute(f"""
                INSERT INTO line4 (timestamp, timezone, {', '.join(LINE_4_SENSORS)})
                VALUES (%s, %s, {', '.join(['%s'] * len(LINE_4_SENSORS))})
            """, line4_values)

            line5_values = [current_timestamp, timezone_offset]
            for sensor in LINE_5_SENSORS:
                temp = sensor_temps[sensor]
                limits = SENSOR_RANGES_LINE5[sensor]
                delta = random.uniform(-0.2, 0.2)
                new_temp = max(limits["min"], min(limits["max"], temp + delta))
                sensor_temps[sensor] = round(new_temp, 2)
                line5_values.append(sensor_temps[sensor])

            cursor.execute(f"""
                INSERT INTO line5 (timestamp, timezone, {', '.join(LINE_5_SENSORS)})
                VALUES (%s, %s, {', '.join(['%s'] * len(LINE_5_SENSORS))})
            """, line5_values)

            connection.commit()
            cursor.close()
            connection.close()
            time.sleep(30)

        except Exception as e:
            logging.error(f"Simulation error: {e}")
            time.sleep(5)

@app.route('/api/live-data/<line>', methods=['GET'])
def get_live_data(line):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        valid_lines = ["line4", "line5"]
        if line not in valid_lines:
            return jsonify({'error': 'Invalid line selected'}), 400

        query = f"SELECT * FROM {line} ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        data = cursor.fetchone()
        cursor.close()
        connection.close()

        if not data:
            return jsonify({'error': 'No live data available'}), 404

        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logging.error(f"Error fetching live data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor-data/<line>/<sensor>', methods=['GET'])
def get_sensor_data(line, sensor):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        valid_lines = ["line4", "line5"]
        if line not in valid_lines:
            return jsonify({'error': 'Invalid line selected'}), 400

        query = f"SELECT timestamp, {sensor} FROM {line} ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        data = cursor.fetchone()
        cursor.close()
        connection.close()

        if not data:
            return jsonify({'error': 'No data available for this sensor'}), 404

        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logging.error(f"Error fetching sensor data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical/<line>', methods=['POST'])
def get_historical_data(line):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        valid_lines = ["line4", "line5"]
        if line not in valid_lines:
            return jsonify({'error': 'Invalid line selected'}), 400

        if request.content_type != "application/json":
            return jsonify({'error': "Unsupported Media Type: Request must be JSON"}), 415

        data = request.get_json()
        length = int(data.get("length", 50))
        search_value = data.get("searchValue", "")
        date_filter = data.get("dateFilter", "")

        query = f"SELECT * FROM {line} WHERE 1=1"
        if date_filter:
            query += f" AND DATE(timestamp) = '{date_filter}'"
        if search_value:
            query += f" AND (timestamp LIKE '%{search_value}%')"

        query += f" ORDER BY timestamp DESC LIMIT {length}"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        connection.close()

        for record in data:
            record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/table-headers', methods=['GET', 'OPTIONS'])
def get_table_headers():
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        tableID = request.args.get('tableID')
        cursor = connection.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {tableID}")
        columns = cursor.fetchall()
        cursor.close()
        connection.close()

        headers = [column[0] for column in columns]
        return jsonify({'success': True, 'headers': headers})

    except Exception as e:
        logging.error(f"Error fetching table headers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/logs', methods=['POST'])
def get_logs():
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)

        if request.content_type != "application/json":
            return jsonify({'error': "Unsupported Media Type: Request must be JSON"}), 415

        data = request.get_json()
        length = int(data.get("length", 50))
        search_value = data.get("searchValue", "")
        date_filter = data.get("dateFilter", "")

        query = "SELECT * FROM logs WHERE 1=1"
        if date_filter:
            query += f" AND DATE(timestamp) = '{date_filter}'"
        if search_value:
            query += f" AND (message LIKE '%{search_value}%' OR type LIKE '%{search_value}%' OR level LIKE '%{search_value}%')"

        query += " ORDER BY id DESC LIMIT %s"
        cursor.execute(query, (length,))
        data = cursor.fetchall()
        cursor.close()
        connection.close()

        for record in data:
            record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logging.error(f"Error fetching historical logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    try:
        data = request.get_json()
        operator_id = data.get('operator_id')
        email = data.get('email')

        if not operator_id or not email:
            return jsonify({'success': False, 'error': 'Operator ID and Email are required'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM user_accounts
            WHERE operator_id = %s AND email = %s
        """, (operator_id, email))

        user = cursor.fetchone()

        if user:
            cursor.execute("DELETE FROM user_accounts WHERE operator_id = %s", (operator_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return jsonify({'success': True, 'message': 'Password reset successfully'})
        else:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': 'Invalid Operator ID or Email'}), 400

    except Exception as e:
        logging.error(f"Error in forgot password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/average-temperature/<line>', methods=['POST'])
def get_average_temperature(line):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        valid_lines = ["line4", "line5"]
        if line not in valid_lines:
            return jsonify({'error': 'Invalid line selected'}), 400

        if request.content_type != "application/json":
            return jsonify({'error': "Unsupported Media Type: Request must be JSON"}), 415

        data = request.get_json()
        period = data.get("period", "day")

        if period == "day":
            time_condition = "timestamp >= NOW() - INTERVAL 1 DAY"
        elif period == "week":
            time_condition = "timestamp >= NOW() - INTERVAL 1 WEEK"
        elif period == "month":
            time_condition = "timestamp >= NOW() - INTERVAL 1 MONTH"
        else:
            return jsonify({'error': 'Invalid period selected'}), 400

        cursor.execute(f"SHOW COLUMNS FROM {line}")
        columns = cursor.fetchall()
        sensor_columns = [col['Field'] for col in columns if col['Field'].startswith('r')]

        avg_query_parts = [f"AVG({sensor}) as avg_{sensor}" for sensor in sensor_columns]
        avg_query = ", ".join(avg_query_parts)

        query = f"SELECT {avg_query} FROM {line} WHERE {time_condition}"
        cursor.execute(query)
        averages = cursor.fetchone()
        cursor.close()
        connection.close()

        return jsonify({'success': True, 'averages': averages}), 200

    except Exception as e:
        logging.error(f"Error fetching average temperature: {e}")
        return jsonify({'error': str(e)}), 500

          
def get_user_details():
    try:
        # Get user ID from session (or pass it directly for testing)
        user_id = session.get('user_id')  # Assuming user is logged in
        
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        conn = db_config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to get user details
        query = "SELECT username, email, created_at FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            return jsonify(user), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT operator_id, email, full_name, admin, active FROM user_accounts WHERE operator_id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return render_template('account.html', user=user)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('login'))
    
@app.route('/api/update-password', methods=['POST', 'OPTIONS'])
def update_password():
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    try:
        data = request.get_json()
        operator_id = data.get('operator_id')
        new_password = data.get('new_password')

        if not operator_id or not new_password:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400

        hashed_pw = generate_password_hash(new_password)

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor()
        cursor.execute("""
            UPDATE user_accounts 
            SET password = %s 
            WHERE operator_id = %s
        """, (hashed_pw, operator_id))
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'success': True})

    except Exception as e:
        logging.error(f"Error updating password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    simulation_thread = threading.Thread(target=generate_temperature_readings, daemon=True)
    simulation_thread.start()
    app.run(debug=True, use_reloader=False)