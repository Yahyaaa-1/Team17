from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from config import Config
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash   
import threading
import time
import logging
import random
from datetime import datetime

app = Flask(__name__)

# CORS configuration
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
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
        print(f"Database connection error: {str(e)}")
        return None
    
# Test removal - redundant code - no value -----------------------
# # Root route
# @app.route('/')
# def home():
#     return jsonify({
#         "message": "Welcome to the API",
#         "status": "running"
#     })

# # Test route
# @app.route('/api/test')
# def test_route():
#     return jsonify({
#         "message": "API is working correctly",
#         "status": "success"
#     })
    
# log event
@app.route('/api/log', methods=['POST', 'OPTIONS'])
def trigger_log():

    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
    
    try:
        data = request.get_json()
        message = data.get('message')
        type = data.get('type', 'INFO')
        log_level = data.get('level', 'admin')
        
        # Call the log_event function directly
        log_event(message, type=type, log_level=log_level)
        
        return jsonify({'success': True, 'message': 'Log event triggered'})
    except Exception as e:
        print(f"Logging error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
def log_event(message, type, log_level):
    try:
        print("Reached log_event method")

        try:
            # Direct database insertion instead of HTTP call
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO logs 
                    (level, type, message) 
                    VALUES (%s, %s, %s)
                """, (log_level, type, message))
                connection.commit()
                cursor.close()
                connection.close()
        except Exception as e:
            print(f"Failed to log event directly: {e}")

    except Exception as e:
        print(f"Failed to log event: {e}")

# Verify employee
@app.route('/api/verify-employee', methods=['POST', 'OPTIONS'])
def verify_employee():

    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        return response

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        email = data.get('email')
        temp_password = data.get('temp_password')

        if not email or not temp_password:
            return jsonify({'success': False, 'error': 'Missing credentials'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM employee_registry 
                WHERE email = %s AND temp_password = %s
            """, (email, temp_password))
            
            employee = cursor.fetchone()
            
            if employee:
                return jsonify({'success': True, 'message': 'Verification successful'})
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        print(f"Error in verify_employee: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():    

    try:
        data = request.get_json()
        operator_id = data.get('operator_id')
        email = data.get('email')

        # Validate input
        if not operator_id or not email:
            return jsonify({
                'success': False, 
                'error': 'Operator ID and Email are required'
            }), 400

        # Database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'success': False, 
                'error': 'Database connection failed'
            }), 500

        cursor = connection.cursor(dictionary=True)

        # Check if operator ID and email match
        cursor.execute("""
            SELECT * FROM user_accounts
            WHERE operator_id = %s AND email = %s
        """, (operator_id, email))

        user = cursor.fetchone()

        if user:
            try:
                cursor.execute("""
                DELETE FROM user_accounts 
                WHERE operator_id = %s
                """, (operator_id,))

                connection.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Password reset successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'error': str(e)
                }), 500
        else:
            return jsonify({
                'success': False, 
                'error': 'Invalid Operator ID or Email'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
# user registration
@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():    

    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        email = data.get('email')
        temp_password = data.get('temp_password')
        new_password = data.get('new_password')

        if not all([email, temp_password, new_password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        
        # First verify the employee
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
        else:
            print(f"Employee details: {employee}")

        # Check if user already exists in user_accounts
        cursor.execute("""
            SELECT * FROM user_accounts 
            WHERE email = %s
        """, (email,))
        
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': 'User already registered'}), 400

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

       # Create new user account
        try:
            cursor.execute("""
                INSERT INTO user_accounts 
                (operator_id,email, full_name, password, admin, active,dark_mode) 
                VALUES (%s, %s, %s, %s, %s,%s,%s)
            """, (employee['operator_id'],email, employee['full_name'], hashed_password, 0, 0,0))

            connection.commit()
        except mysql.connector.Error as err:
          
            return jsonify({'success': False, 'error': 'Database error occurred'}), 500
        finally:
            cursor.close()
            connection.close()

        log_event(f"New user registered: {email}", type='INFO', log_level='admin')
        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == "OPTIONS":
        return jsonify({"success": True})

    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
    
    try:
        data = request.get_json()
        
        if not data:
            # Log empty data attempt
            log_event("Login attempt with no data", type='warning', log_level='admin')
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            # Log missing credentials
            log_event(f"Login attempt with missing credentials. Email: {email}", 
                      type='WARNING', 
                      log_level='admin')
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        connection = get_db_connection()
        if not connection:
            # Log database connection failure
            log_event("Database connection failed during login", 
                      type='ERROR', 
                      log_level='admin')
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = connection.cursor(dictionary=True)
            
            # Check if user exists and verify password
            cursor.execute("""
                SELECT * FROM user_accounts 
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()

            if not user:
                cursor.close()
                connection.close()
                # Log non-existent email attempt
                log_event(f"Login attempt for non-existent email: {email}", type='WARNING', log_level='admin')
                return jsonify({'success': False, 'error': 'Invalid email'}), 401

            # Check password
            if not check_password_hash(user['password'], password):
                cursor.close()
                connection.close()
                # Log failed password attempt
                log_event(f"Failed password attempt for email: {email}", type='WARNING',log_level='admin')
                return jsonify({'success': False, 'error': 'Invalid password'}), 401

            # Check if user is active
            if not user['active']:
                cursor.close()
                connection.close()
                # Log inactive user login attempt
                log_event(f"Login attempt for inactive user: {email}", type='INFO', log_level='admin')
                return jsonify({
                    'success': False, 
                    'error': 'Account not yet approved. Please contact administrator.',
                    'active': False
                }), 403

            # Successful login
            cursor.close()
            connection.close()

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

        except Exception as inner_error:
            # Log any unexpected inner errors
            log_event(f"Unexpected error during login: {str(inner_error)}", type='ERROR', log_level='admin')
            print(f"Login inner error details: {inner_error}")
            
            # Ensure connection is closed
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            
            return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500

    except Exception as outer_error:
        # Log any unexpected outer errors
        log_event(f"Unexpected outer error during login: {str(outer_error)}", type='ERROR', log_level='admin')
        
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500
    
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

        cursor.execute("""
            SELECT * FROM user_accounts 
        """)
        
        user_accounts = cursor.fetchall()

        cursor.close()
        connection.close()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({
            'success': True, 
            'message': 'Retrieved user accounts successfully',
            'user_accounts': user_accounts
        })

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

        cursor.execute("""
            SELECT * FROM employee_registry 
        """)
        
        employee_registry = cursor.fetchall()

        cursor.close()
        connection.close()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({
            'success': True, 
            'message': 'Retrieved user accounts successfully',
            'employee_registry': employee_registry
        })

# Get user status
@app.route('/api/admin/toggle-user-status', methods=['POST', 'OPTIONS'])
def toggleUserStatus():
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')

        print(operator_id)
       

        if not all([operator_id]):
            return jsonify({'success': False, 'error': 'Missing Operator id'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        
        try:
            data = request.get_json()
            operator_id = data.get('operator_id')
            admin_ID = data.get('admin_ID')

            cursor = connection.cursor(dictionary=True)
            
            # Get user active status
            cursor.execute("""SELECT active 
                           FROM user_accounts 
                           WHERE operator_id = %s""", (operator_id,))
            
            user = cursor.fetchone()
            
            # Overwrite user active status
            current_status = int(user['active'])  
            if current_status == 0:
                new_status = 1
            else:
                new_status = 0

            # Update query
            query = """
                UPDATE user_accounts
                SET active = %s
                WHERE operator_id = %s
            """
            
            cursor.execute(query, (new_status, operator_id))
            connection.commit()

            log_event(f"User {operator_id} status changed to {new_status} by Admin - {admin_ID}", type='INFO', log_level='admin')
            return jsonify({
                'success': True, 
                'message': f'User status updated to {"active" if new_status == 1 else "inactive"}',
                'new_status': new_status
            })

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'success': False, 'error': 'Database error occurred'}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    
# Get admin status
@app.route('/api/admin/toggle-admin-status', methods=['POST', 'OPTIONS'])
def toggleAdminStatus():
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')

        print(operator_id)
       

        if not all([operator_id]):
            return jsonify({'success': False, 'error': 'Missing Operator id'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        
        try:
            data = request.get_json()
            operator_id = data.get('operator_id')
            admin_ID = data.get('admin_ID')

            cursor = connection.cursor(dictionary=True)
            
            # Get admin status
            cursor.execute("""SELECT admin 
                           FROM user_accounts 
                           WHERE operator_id = %s""", (operator_id,))
            
            user = cursor.fetchone()
            
            # Overwrite user active status
            current_status = int(user['admin'])  

            if current_status == 0:
                new_status = 1
            else:
                new_status = 0

            # Update query
            query = """
                UPDATE user_accounts
                SET admin = %s
                WHERE operator_id = %s
            """
            
            cursor.execute(query, (new_status, operator_id))
            connection.commit()

            log_event(f"User {operator_id} Admin status changed to {new_status} by Admin - {admin_ID}", type='INFO', log_level='admin')
            return jsonify({
                'success': True, 
                'message': f'User admin status updated to {"admin" if new_status == 1 else "operator"}',
                'admin': new_status
            })

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'success': False, 'error': 'Database error occurred'}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
# Delete user account
@app.route('/api/admin/delete-user', methods=['POST', 'OPTIONS'])
def deleteUser():
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')

        print(operator_id)
       

        if not [operator_id]:
            return jsonify({'success': False, 'error': 'Missing Operator id'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            data = request.get_json()
            operator_id = data.get('operator_id')

            cursor = connection.cursor(dictionary=True)

            # First verify the user exists
            cursor.execute("SELECT * FROM user_accounts WHERE operator_id = %s", (operator_id,))
            user = cursor.fetchone()
            print(f"User before deletion: {user}")

            if not user:
                return jsonify({
                    'success': False,
                    'message': f'User {operator_id} not found'
                }), 404

            # Delete query
            query = "DELETE FROM user_accounts WHERE operator_id = %s"
            print(f"Executing delete query for operator: {operator_id}")
            
            cursor.execute(query, (operator_id,))
            affected_rows = cursor.rowcount
            print(f"Rows affected by delete: {affected_rows}")
            
            connection.commit()

            # Verify deletion
            cursor.execute("SELECT * FROM user_accounts WHERE operator_id = %s", (operator_id,))
            verify = cursor.fetchone()
            print(f"User after deletion attempt: {verify}")

            if affected_rows > 0 and verify is None:

                log_event(f"User {operator_id} deleted by admin - {admin_ID}", type='WARNING', log_level='admin')

                return jsonify({
                    'success': True,
                    'message': f'User {operator_id} has been deleted',
                    'rows_affected': affected_rows
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Delete operation failed for user {operator_id}',
                    'rows_affected': affected_rows
                }), 500

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'success': False, 'error': str(err)}), 500
        finally:
            cursor.close()
            connection.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Delete employee
@app.route('/api/admin/delete-employee', methods=['POST', 'OPTIONS'])
def deleteEmployee():
        
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        operator_id = data.get('operator_id')
        admin_ID = data.get('admin_ID')


        print(operator_id)
       

        if not [operator_id]:
            return jsonify({'success': False, 'error': 'Missing Operator id'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            data = request.get_json()
            operator_id = data.get('operator_id')
            print(f"Attempting to delete operator: {operator_id}")

            cursor = connection.cursor(dictionary=True)
           

            # First verify the user exists
            cursor.execute("SELECT * FROM employee_registry WHERE operator_id = %s", (operator_id,))
            user = cursor.fetchone()
            print(f"User before deletion: {user}")

            if not user:
                return jsonify({
                    'success': False,
                    'message': f'User {operator_id} not found'
                }), 404

            # Then delete from employee_registry
            cursor.execute("DELETE FROM employee_registry WHERE operator_id = %s", (operator_id,))
            employee = cursor.rowcount
            print(f"Rows affected in employee_registry: {employee}")

            connection.commit()

            # Verify deletion
            cursor.execute("SELECT * FROM employee_registry WHERE operator_id = %s", (operator_id,))
            verify = cursor.fetchone()

            if verify is None:
                log_event(f"Employee Reg {operator_id} deleted by admin - {admin_ID}", type='WARNING', log_level='admin')
                return jsonify({
                    'success': True,
                    'message': f'User {operator_id} has been deleted',
                    'employee_rows_affected': employee
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Delete operation failed for user {operator_id}'
                }), 500

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'success': False, 'error': str(err)}), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

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

        # Query to get column names
        cursor.execute(f"SHOW COLUMNS FROM {tableID}")
        columns = cursor.fetchall()

        cursor.close()
        connection.close()

        # Extract column names
        headers = [column[0] for column in columns]

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    return jsonify({
        'success': True,
        'headers': headers
    })



# Delete user account
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
# Set initial temperatures to typical operating values
sensor_temps = {}
for sensor in LINE_4_SENSORS:
    sensor_temps[sensor] = SENSOR_RANGES_LINE4[sensor]["avg"]
for sensor in LINE_5_SENSORS:
    sensor_temps[sensor] = SENSOR_RANGES_LINE5[sensor]["avg"]

def generate_temperature_readings():
    while True:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Get current timestamp
            current_timestamp = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

            # Get timezone offset from month
            def get_timezone_offset():
                current_month = time.localtime().tm_mon

                # Daylight savings from end march to Oct
                if 4 <= current_month <= 10:
                    return "+01"
                else:
                    return "+00"

            timezone_offset = get_timezone_offset()

            # Line 4 sensor readings
            line4_values = [current_timestamp, timezone_offset]
            for sensor in LINE_4_SENSORS:
                temp = sensor_temps[sensor]
                limits = SENSOR_RANGES_LINE4[sensor]
                
                # Small random fluctuation
                delta = random.uniform(-0.2, 0.2)
                new_temp = temp + delta
                
                # Keep within sensor limits
                new_temp = max(limits["min"], min(limits["max"], new_temp))
                sensor_temps[sensor] = round(new_temp, 2)
                line4_values.append(sensor_temps[sensor])

            try:
                cursor.execute(f"""
                    INSERT INTO line4 (timestamp, timezone, {', '.join(LINE_4_SENSORS)})
                    VALUES (%s, %s, {', '.join(['%s'] * len(LINE_4_SENSORS))})
                """, line4_values)
            except Exception as e:
                print(f"Error inserting line 4 data: {e}")
                print("Parameters:", line4_values)
                print("Number of parameters:", len(line4_values))
                raise
                        
            # Line 5 sensor readings  
            line5_values = [current_timestamp, timezone_offset]
            for sensor in LINE_5_SENSORS:
                temp = sensor_temps[sensor]
                limits = SENSOR_RANGES_LINE5[sensor]
                
                delta = random.uniform(-0.2, 0.2)
                new_temp = temp + delta
                new_temp = max(limits["min"], min(limits["max"], new_temp))
                sensor_temps[sensor] = round(new_temp, 2)
                line5_values.append(sensor_temps[sensor])

            try:
                cursor.execute(f"""
                    INSERT INTO line5 (timestamp, timezone, {', '.join(LINE_5_SENSORS)})
                    VALUES (%s, %s, {', '.join(['%s'] * len(LINE_5_SENSORS))})
                """, line5_values)
            except Exception as e:
                print(f"Error inserting line 5 data: {e}")
                print("Parameters:", line5_values)
                print("Number of parameters:", len(line5_values))
                raise

            connection.commit()
            print(f"Line 4: {dict(zip(LINE_4_SENSORS, line4_values[2:]))}")
            print(f"Line 5: {dict(zip(LINE_5_SENSORS, line5_values[2:]))}")

            cursor.close()
            connection.close()
            time.sleep(30)

        except Exception as e:
            print(f"Simulation error: {e}")
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

        if not data:
            return jsonify({'error': 'No live data available'}), 404

        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        print(f"Error fetching live data: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
            
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

        # Fetch the most recent reading for the specified sensor
        query = f"SELECT timestamp, {sensor} FROM {line} ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        data = cursor.fetchone()

        if not data:
            return jsonify({'error': 'No data available for this sensor'}), 404

        # Format the timestamp
        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        print(f"Error fetching sensor data: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/sensor/<line>/<sensor>')
def sensor_page(line, sensor):
    return render_template('sensor-data.html', line=line, sensor=sensor)

  
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

        for record in data:
            record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()


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

        # Base query
        query = "SELECT * FROM logs WHERE 1=1"

        # Apply filters
        if date_filter:
            query += f" AND DATE(timestamp) = '{date_filter}'"
        if search_value:
            query += f" AND (message LIKE '%{search_value}%' OR type LIKE '%{search_value}%' OR level LIKE '%{search_value}%')"

        # Sorting and limiting
        query += " ORDER BY id DESC LIMIT %s"
        
        cursor.execute(query, (length,))
        data = cursor.fetchall()

        # Format timestamp
        for record in data:
            record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        print(f"Error fetching historical logs: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

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
        period = data.get("period", "day")  # Default to 'day'

        # Determine the time range based on the period
        if period == "day":
            time_condition = "timestamp >= NOW() - INTERVAL 1 DAY"
        elif period == "week":
            time_condition = "timestamp >= NOW() - INTERVAL 1 WEEK"
        elif period == "month":
            time_condition = "timestamp >= NOW() - INTERVAL 1 MONTH"
        else:
            return jsonify({'error': 'Invalid period selected'}), 400

        # Get the column names for the sensors
        cursor.execute(f"SHOW COLUMNS FROM {line}")
        columns = cursor.fetchall()
        sensor_columns = [col['Field'] for col in columns if col['Field'].startswith('r')]

        # Construct the query to calculate averages
        avg_query_parts = [f"AVG({sensor}) as avg_{sensor}" for sensor in sensor_columns]
        avg_query = ", ".join(avg_query_parts)

        query = f"SELECT {avg_query} FROM {line} WHERE {time_condition}"

           # Debugging: Print the final query
        print(f"Executing query: {query}")

        cursor.execute(query)
        averages = cursor.fetchone()

        return jsonify({'success': True, 'averages': averages}), 200

    except Exception as e:
        print(f"Error fetching average temperature: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
if __name__ == '__main__':
    simulation_thread = threading.Thread(target=generate_temperature_readings, daemon=True)
    simulation_thread.start()
    app.run(debug=True, use_reloader=False)

    