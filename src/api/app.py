from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import mysql.connector
from config import Config
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash   
import logging
import threading
import time
import random

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

# Root route
@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the API",
        "status": "running"
    })

# Test route
@app.route('/api/test')
def test_route():
    return jsonify({
        "message": "API is working correctly",
        "status": "success"
    })

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

        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# user Login
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

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
            return jsonify({'success': False, 'error': 'Invalid email'}), 401

        # Check password
        if not check_password_hash(user['password'], password):
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': 'Invalid password'}), 401

        # Check if user is active
        if not user['active']:
            cursor.close()
            connection.close()
            return jsonify({
                'success': False, 
                'error': 'Account not yet approved. Please contact administrator.',
                'active': False
            }), 403

        # Successful login
        cursor.close()
        connection.close()

        return jsonify({
            'success': True, 
            'message': 'Login successful',
            'active': True,
            'operator_id': user['operator_id'],
            'email' : user['email'],
            'full_name': user['full_name'],
            'dark_mode': user['dark_mode'],
            'is_admin': user['admin']
        })

    except Exception as e:
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

        print(operator_id)
       

        if not all([operator_id]):
            return jsonify({'success': False, 'error': 'Missing Operator id'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        
        try:
            data = request.get_json()
            operator_id = data.get('operator_id')

            cursor = connection.cursor(dictionary=True)
            
            # Get user active status
            cursor.execute("""SELECT active 
                           FROM user_accounts 
                           WHERE operator_id = %s""", (operator_id,))
            
            user = cursor.fetchone()
            print("Current user status:", user['active'], "Type:", type(user['active']))

            # Overwrite user active status
            current_status = int(user['active'])  # Convert to int if it's a string
            if current_status == 0:
                new_status = 1
            else:
                new_status = 0

            # new_status = 0 if current_status == 1 else 1
            # print(f"Current status: {current_status} -> New status: {new_status}")

            # Update query
            query = """
                UPDATE user_accounts
                SET active = %s
                WHERE operator_id = %s
            """
            # print("Query:", query)
            # print("Parameters:", (new_status, operator_id))
            
            cursor.execute(query, (new_status, operator_id))
            connection.commit()

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
        print(f"DB Connection failed: {str(e)}")
        return None

def generate_temperature_readings():
    while True:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

              # Determine timezone offset based on the season
            def get_timezone_offset():
                
                # You can customize this logic based on your specific requirements
                current_month = time.localtime().tm_mon
                
                # Typically, daylight saving time (summer time) is from March to October
                if 4 <= current_month <= 10:
                    return "+01"
                else:
                    return "+00"

            # Store line 5 data with hardcoded timestamp and timezone
            timezone_offset = get_timezone_offset()
            

            # Line 4 sensor readings
            line4_values = []
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
            line5_values = []
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

            print("LINE_5_SENSORS:", LINE_5_SENSORS)
            print("Number of sensors:", len(LINE_5_SENSORS))
            print("line5_values:", line5_values)
            print("Number of values:", len(line5_values))

            connection.commit()
            print(f"Line 4: {dict(zip(LINE_4_SENSORS, line4_values))}")
            print(f"Line 5: {dict(zip(LINE_5_SENSORS, line5_values))}")

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

if __name__ == '__main__':
    simulation_thread = threading.Thread(target=generate_temperature_readings, daemon=True)
    simulation_thread.start()
    app.run(debug=True, use_reloader=False)

    