from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import time
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])
# -------------------- HELPERS --------------------
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def log_event(message, type='INFO', log_level='admin'):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO logs (level, type, message) 
                VALUES (%s, %s, %s)
            """, (log_level, type, message))
            connection.commit()
            cursor.close()
            connection.close()
    except Exception as e:
        print(f"Log error: {e}")

def success(msg, **kwargs):
    return jsonify({"success": True, "message": msg, **kwargs})

def error(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

def handle_options():
    return '', 204

# -------------------- ROUTES --------------------

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/api/log', methods=['POST', 'OPTIONS'])
def trigger_log():
    if request.method == 'OPTIONS': return handle_options()
    data = request.get_json()
    log_event(data.get('message'), type=data.get('type', 'INFO'), log_level=data.get('level', 'admin'))
    return success("Log event triggered")

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return handle_options()
    data = request.get_json()
    full_name, email, new_password = data.get('full_name'), data.get('email'), data.get('new_password')
    if not all([full_name, email, new_password]): return error("Missing fields")
    conn = get_db_connection()
    if not conn: return error("DB connection failed", 500)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_accounts WHERE email = %s", (email,))
    if cursor.fetchone(): return error("User already exists")
    hashed_pw = generate_password_hash(new_password)
    cursor.execute("""
        INSERT INTO user_accounts (email, full_name, password, admin, active, dark_mode)
        VALUES (%s, %s, %s, 0, 0, 0)
    """, (email, full_name, hashed_pw))
    conn.commit()
    cursor.close()
    conn.close()
    log_event(f"New user registered: {email}")
    return success("Registration successful")

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return handle_options()

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return error("Email and password required")

    conn = get_db_connection()
    if not conn:
        return error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_accounts WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        cursor.close()
        conn.close()
        log_event(f"User logged in: {email}")
        return jsonify({
            "success": True,
            'message': 'Login successful',
                'active': True,
                'operator_id': user['operator_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'dark_mode': user['dark_mode'],
                'is_admin': user['admin']
        })
    else:
        cursor.close()
        conn.close()
        return error("Invalid email or password", 401)

@app.route('/api/historical-data/<line>', methods=['POST'])
def get_historical_data(line):
    conn = get_db_connection()
    if not conn: return error("Database connection failed", 500)
    cursor = conn.cursor(dictionary=True)
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
    results = cursor.fetchall()
    for record in results:
        record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    cursor.close()
    conn.close()
    return jsonify({"success": True, "data": results}), 200

@app.route('/api/logs', methods=['POST'])
def get_logs():
    conn = get_db_connection()
    if not conn:
        return error("Database connection failed", 500)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100")
    results = cursor.fetchall()
    for record in results:
        record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    cursor.close()
    conn.close()
    return jsonify({"success": True, "data": results})

@app.route('/api/live-data/<line>', methods=['GET', 'OPTIONS'])
def get_live_data(line):
    if request.method == 'OPTIONS': return handle_options()
    try:
        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM {line} ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        data = cursor.fetchone()
        if not data:
            return error('No live data available', 404)
        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        return error(str(e), 500)
    finally:
        if connection: connection.close()

@app.route('/api/admin/user-accounts', methods=['GET'])
def get_user_accounts():
    """Get all user accounts"""
        
    try:
        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
            SELECT * FROM user_accounts 
            """)
            
            user_accounts = cursor.fetchall()

            # Format dates if needed
            for account in user_accounts:
                if 'created_at' in account and account['created_at']:
                    account['created_at'] = account['created_at'].strftime("%Y-%m-%d %H:%M:%S")

            log_event("Admin retrieved all user accounts", type='INFO', log_level='admin')
            return success("Retrieved user accounts successfully", user_accounts=user_accounts)

        except mysql.connector.Error as db_err:
            log_event(f"Database error in get_user_accounts: {str(db_err)}", type='ERROR', log_level='admin')
            return error(f'Database error: {str(db_err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in get_user_accounts: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 500)
# Admin user management endpoints
def validate_admin_request(data):
    """Validate common admin request data"""
    if not data:
        return error('No data received')
    
    operator_id = data.get('operator_id')
    admin_id = data.get('admin_ID')
    
    if not operator_id:
        return error('Missing operator ID')
        
    return None, operator_id, admin_id
@app.route('/api/admin/toggle-admin-status', methods=['POST', 'OPTIONS'])
def toggle_admin_status():
    """Toggle user's admin status"""
    if request.method == 'OPTIONS':
        return handle_options()
    
    if request.method != 'POST':
        return error('Method not allowed', 405)
        
    try:
        data = request.get_json()
        if not data:
            return error('No data received', 400)
            
        operator_id = data.get('operator_id')
        admin_id = data.get('admin_ID')

        if not operator_id:
            return error('Missing Operator id', 400)
        
        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get admin status
            cursor.execute("""
                SELECT admin 
                FROM user_accounts 
                WHERE operator_id = %s
            """, (operator_id,))
            
            user = cursor.fetchone()
            if not user:
                return error('User not found', 404)
            
            # Toggle admin status
            current_status = int(user['admin'])
            new_status = 1 if current_status == 0 else 0

            # Update admin status
            cursor.execute("""
                UPDATE user_accounts
                SET admin = %s
                WHERE operator_id = %s
            """, (new_status, operator_id))
            
            connection.commit()

            # Log the change
            log_event(
                f"User {operator_id} Admin status changed to {new_status} by Admin - {admin_id}", 
                type='INFO', 
                log_level='admin'
            )

            return success(
                f'User admin status updated to {"admin" if new_status == 1 else "operator"}',
                admin=new_status
            )

        except mysql.connector.Error as err:
            log_event(f"Database error in toggle_admin_status: {str(err)}", type='ERROR', log_level='admin')
            return error('Database error occurred', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in toggle_admin_status: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 400)
    
@app.route('/api/admin/toggle-user-admin', methods=['POST', 'OPTIONS'])
def toggle_user_admin():
    """Toggle user's admin status"""
    if request.method == 'OPTIONS':
        return handle_options()

    try:
        # Validate request
        validation_error, operator_id, admin_id = validate_admin_request(request.get_json())
        if validation_error:
            return validation_error

        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get current admin status
            cursor.execute("""
                SELECT admin 
                FROM user_accounts 
                WHERE operator_id = %s
            """, (operator_id,))
            
            user = cursor.fetchone()
            if not user:
                return error('User not found', 404)

            # Toggle status
            new_status = 0 if int(user['admin']) == 1 else 1
            
            # Update status
            cursor.execute("""
                UPDATE user_accounts
                SET admin = %s
                WHERE operator_id = %s
            """, (new_status, operator_id))
            
            connection.commit()

            status_text = "admin" if new_status == 1 else "not admin"
            log_event(
                f"User {operator_id} admin status changed to {status_text} by Admin {admin_id}", 
                type='INFO', 
                log_level='admin'
            )

            return success(
                f'User status updated to {status_text}',
                new_status=new_status
            )

        except mysql.connector.Error as err:
            log_event(f"Database error in toggle_user_admin: {str(err)}", type='ERROR', log_level='admin')
            return error(f'Database error: {str(err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in toggle_user_admin: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 500)

@app.route('/api/admin/delete-user', methods=['POST', 'OPTIONS'])
def delete_user():
    """Delete user account"""
    if request.method == 'OPTIONS':
        return handle_options()

    try:
        # Validate request
        validation_error, operator_id, admin_id = validate_admin_request(request.get_json())
        if validation_error:
            return validation_error

        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)

            # Verify user exists
            cursor.execute("""
                SELECT operator_id, email 
                FROM user_accounts 
                WHERE operator_id = %s
            """, (operator_id,))
            
            user = cursor.fetchone()
            if not user:
                return error(f'User {operator_id} not found', 404)

            # Delete user
            cursor.execute("""
                DELETE FROM user_accounts 
                WHERE operator_id = %s
            """, (operator_id,))
            
            affected_rows = cursor.rowcount
            connection.commit()

            if affected_rows > 0:
                log_event(
                    f"User {operator_id} deleted by admin {admin_id}", 
                    type='WARNING', 
                    log_level='admin'
                )
                return success(
                    f'User {operator_id} has been deleted',
                    rows_affected=affected_rows
                )
            else:
                return error('Delete operation failed', 500)

        except mysql.connector.Error as err:
            log_event(f"Database error in delete_user: {str(err)}", type='ERROR', log_level='admin')
            return error(f'Database error: {str(err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in delete_user: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 500)   

@app.route('/api/admin/delete-sensor', methods=['POST', 'OPTIONS'])
def delete_sensor():
    """Delete a sensor column from specified table"""
    if request.method == 'OPTIONS':
        return handle_options()
    
    if request.method != 'POST':
        return error('Method not allowed', 405)
        
    try:
        data = request.get_json()
        if not data:
            return error('No data received', 400)
            
        sensor = data.get('sensorName')
        table_id = data.get('tableID')

        # Validate inputs
        if not sensor:
            return error('Missing Sensor Name', 400)
        
        if not table_id:
            return error('Missing Table ID', 400)
    

        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)

            # Check if column exists
            cursor.execute(f"SHOW COLUMNS FROM {table_id} LIKE %s", (sensor,))
            column_exists = cursor.fetchone()
            
            if not column_exists:
                return error(f'Sensor {sensor} does not exist in the table', 400)

            # Delete the sensor column
            cursor.execute(f"ALTER TABLE {table_id} DROP COLUMN {sensor}")
            connection.commit()
            
            log_event(
                f"Sensor {sensor} deleted from table {table_id}", 
                type='WARNING', 
                log_level='admin'
            )

            return success(f'Sensor {sensor} deleted from {table_id}')

        except mysql.connector.Error as err:
            log_event(f"Database error in delete_sensor: {str(err)}", type='ERROR', log_level='admin')
            return error(str(err), 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in delete_sensor: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 400)
    
@app.route('/api/admin/toggle-user-status', methods=['POST', 'OPTIONS'])
def toggle_user_status():
    """Toggle user's active status"""
    if request.method == 'OPTIONS':
        return handle_options()

    try:
        # Validate request
        validation_error, operator_id, admin_id = validate_admin_request(request.get_json())
        if validation_error:
            return validation_error

        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get current active status
            cursor.execute("""
                SELECT active, email 
                FROM user_accounts 
                WHERE operator_id = %s
            """, (operator_id,))
            
            user = cursor.fetchone()
            if not user:
                return error('User not found', 404)

            # Toggle status
            new_status = 0 if int(user['active']) == 1 else 1
            
            # Update status
            cursor.execute("""
                UPDATE user_accounts
                SET active = %s
                WHERE operator_id = %s
            """, (new_status, operator_id))
            
            connection.commit()

            status_text = "active" if new_status == 1 else "inactive"
            log_event(
                f"User {user['email']} (ID: {operator_id}) status changed to {status_text}", 
                type='INFO', 
                log_level='admin'
            )

            return success(
                f'User status updated to {status_text}',
                new_status=new_status
            )

        except mysql.connector.Error as err:
            log_event(f"Database error in toggle_user_status: {str(err)}", type='ERROR', log_level='admin')
            return error(f'Database error: {str(err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in toggle_user_status: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 500)
   
# Password Update
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

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'connection' in locals(): connection.close()
    
    
@app.route('/api/admin/update-user-details', methods=['POST', 'OPTIONS'])
def update_user_details():
    """Update user's email and full name"""
    if request.method == 'OPTIONS':
        return handle_options()

    try:
        data = request.get_json()
        if not data:
            return error('No data received')

        # Extract and validate required fields
        operator_id = data.get('operator_id')
        new_email = data.get('Nemail')
        new_fullname = data.get('Nfullname')

        missing_fields = []
        if not operator_id: missing_fields.append('Operator ID')
        if not new_email: missing_fields.append('Email')
        if not new_fullname: missing_fields.append('Full Name')

        if missing_fields:
            return error(f'Missing fields: {", ".join(missing_fields)}')

        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor(dictionary=True)

            # Verify user exists and get current details
            cursor.execute("""
                SELECT email, full_name 
                FROM user_accounts 
                WHERE operator_id = %s
            """, (operator_id,))
            
            user = cursor.fetchone()
            if not user:
                return error('User not found', 404)

            # Check if email is already in use by another user
            cursor.execute("""
                SELECT operator_id 
                FROM user_accounts 
                WHERE email = %s AND operator_id != %s
            """, (new_email, operator_id))
            
            if cursor.fetchone():
                return error('Email already in use by another user')

            # Update user details
            cursor.execute("""
                UPDATE user_accounts
                SET email = %s, full_name = %s
                WHERE operator_id = %s
            """, (new_email, new_fullname, operator_id))
            
            connection.commit()

            log_event(
                f"User details updated - ID: {operator_id}, "
                f"Email: {user['email']} -> {new_email}, "
                f"Name: {user['full_name']} -> {new_fullname}",
                type='INFO',
                log_level='admin'
            )

            return success('User details updated successfully')

        except mysql.connector.Error as err:
            log_event(f"Database error in update_user_details: {str(err)}", type='ERROR', log_level='admin')
            return error(f'Database error: {str(err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        log_event(f"Error in update_user_details: {str(e)}", type='ERROR', log_level='admin')
        return error(str(e), 500)
@app.route('/api/admin/table-headers', methods=['GET', 'OPTIONS'])
def get_table_headers():
    """Get column headers for specified table"""
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
# Forcast Data
@app.route('/api/forecasted-data/<line>', methods=['GET', 'OPTIONS'])
def get_forecasted_data(line):
    if request.method == 'OPTIONS':
        return handle_options()        
    try:
        # Validate line parameter
        valid_lines = ["line4", "line5"]
        if line not in valid_lines:
            return error('Invalid line selected')
        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)
        try:
            cursor = connection.cursor(dictionary=True)            
            # Get forecasted data
            query = f"SELECT * FROM forecasted{line} ORDER BY forecast_time ASC"
            cursor.execute(query)
            data = cursor.fetchall()
            if not data:
                return error('No forecasted data available', 404)
            # Format timestamps in response
            formatted_data = [
                {
                    **record,
                    'forecast_time': record['forecast_time'].strftime("%Y-%m-%d %H:%M:%S")
                } for record in data
            ]
            log_event(f"Forecasted data retrieved for {line}", type='INFO')
            return jsonify({
                'success': True,
                'data': formatted_data
            }), 200
        except mysql.connector.Error as db_err:
            log_event(f"Database error in forecast data: {str(db_err)}", type='ERROR')
            return error(f'Database error: {str(db_err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()
    except Exception as e:
        log_event(f"Error in forecast data: {str(e)}", type='ERROR')
        return error(str(e), 500)

@app.route('/api/historical/<line>/<sensor>', methods=['GET', 'OPTIONS'])
def get_historical_data_sensor(line, sensor):
    if request.method == 'OPTIONS': return handle_options()
    try:
        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)
        cursor = connection.cursor(dictionary=True)

        length = request.args.get('length', default=50, type=int)
        search_value = request.args.get('searchValue', default='', type=str)
        date_filter = request.args.get('dateFilter', default='', type=str)
        start_date_time = request.args.get('startDateTime', default='', type=str)
        end_date_time = request.args.get('endDateTime', default='', type=str)

        query = f"SELECT timestamp, {sensor} as value FROM {line} WHERE 1=1"
        if date_filter:
            query += f" AND DATE(timestamp) = '{date_filter}'"
        if start_date_time and end_date_time:
            query += f" AND timestamp BETWEEN '{start_date_time}' AND '{end_date_time}'"
        if search_value:
            query += f" AND (timestamp LIKE '%{search_value}%')"
        query += f" ORDER BY timestamp DESC LIMIT {length}"

        cursor.execute(query)
        data = cursor.fetchall()
        formatted = [
            {
                'timestamp': record['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                'value': float(record['value'])
            } for record in data
        ]
        return jsonify({'success': True, 'data': formatted}), 200
    except Exception as e:
        return error(str(e), 500)
    finally:
        if connection: connection.close()

@app.route('/api/sensor-data/<line>/<sensor>', methods=['GET', 'OPTIONS'])
def get_sensor_data(line, sensor):
    if request.method == 'OPTIONS': return handle_options()
    try:
        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT timestamp, {sensor} FROM {line} ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        data = cursor.fetchone()
        if not data:
            return error('No data available for this sensor', 404)
        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        return error(str(e), 500)
    finally:
        if connection: connection.close()

@app.route('/api/update-dark-mode', methods=['POST', 'OPTIONS'])
def update_dark_mode():
    if request.method == 'OPTIONS': 
        return handle_options()
        
    try:
        data = request.get_json()
        if not data:
            return error('No data received')

        operator_id = data.get('operator_id')
        dark_mode = data.get('dark_mode', 0)  # Default to light mode

        if not operator_id:
            return error('Missing operator ID')

        connection = get_db_connection()
        if not connection:
            return error('Database connection failed', 500)

        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE user_accounts
                SET dark_mode = %s
                WHERE operator_id = %s
            """, (dark_mode, operator_id))
            
            connection.commit()
            
            log_event(f"Dark mode preference updated for user {operator_id} to {dark_mode}")
            return success('Dark mode preference updated')

        except mysql.connector.Error as err:
            return error(f'Database error: {str(err)}', 500)
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    except Exception as e:
        return error(str(e), 500)
    
# Generate Live Temp

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

def get_timezone_offset():
    """Determine timezone offset based on month (DST aware)"""
    current_month = time.localtime().tm_mon
    return "+01" if 4 <= current_month <= 10 else "+00"

def generate_sensor_reading(sensor, ranges):
    """Generate a single sensor reading within specified ranges"""
    avg_temp = ranges[sensor]["avg"]
    fluctuation = avg_temp * 0.02  # 2% fluctuation
    new_temp = random.uniform(avg_temp - fluctuation, avg_temp + fluctuation)
    
    # Keep within sensor limits
    limits = ranges[sensor]
    new_temp = max(limits["min"], min(limits["max"], new_temp))
    return round(new_temp, 2)

def insert_line_readings(cursor, line_number, sensors, ranges, timestamp, timezone):
    """Insert readings for a specific line"""
    values = [timestamp, timezone]
    values.extend([generate_sensor_reading(sensor, ranges) for sensor in sensors])
    
    try:
        query = f"""
            INSERT INTO line{line_number} 
            (timestamp, timezone, {', '.join(sensors)})
            VALUES (%s, %s, {', '.join(['%s'] * len(sensors))})
        """
        cursor.execute(query, values)
        
        # Log the readings
        readings_dict = dict(zip(sensors, values[2:]))
        print(f"Line {line_number}: {readings_dict}")
        
    except Exception as e:
        log_event(f"Error inserting line {line_number} data: {str(e)}", type='ERROR')
        print(f"Error inserting line {line_number} data: {e}")
        print("Parameters:", values)
        print("Number of parameters:", len(values))
        raise

def generate_temperature_readings():
    """Main temperature reading generation loop"""
    while True:
        connection = None
        cursor = None
        
        try:
            connection = get_db_connection()
            if not connection:
                raise Exception("Failed to establish database connection")
                
            cursor = connection.cursor()
            
            # Generate timestamp and timezone
            current_timestamp = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
            timezone_offset = get_timezone_offset()
            
            # Generate and insert readings for both lines
            insert_line_readings(cursor, 4, LINE_4_SENSORS, SENSOR_RANGES_LINE4, 
                               current_timestamp, timezone_offset)
            insert_line_readings(cursor, 5, LINE_5_SENSORS, SENSOR_RANGES_LINE5, 
                               current_timestamp, timezone_offset)
            
            connection.commit()
            log_event("Temperature readings generated successfully", type='INFO')
            
            time.sleep(30)  # Wait for next reading cycle
            
        except Exception as e:
            log_event(f"Simulation error: {str(e)}", type='ERROR')
            print(f"Simulation error: {e}")
            time.sleep(5)  # Shorter wait time on error
            
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

# -------------------- ENTRY POINT --------------------
if __name__ == '__main__':
    simulation_thread = threading.Thread(target=generate_temperature_readings, daemon=True)
    simulation_thread.start()
    app.run(debug=True, use_reloader=False)