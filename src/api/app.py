# Minimal refactor: only cleaning up redundancy and creating helper functions

from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

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
            "user": {
                "email": user['email'],
                "full_name": user['full_name'],
                "operator_id": user['operator_id'],
                "admin": user['admin'],
                "active": user['active'],
                "dark_mode": user['dark_mode']
            }
        })
    else:
        cursor.close()
        conn.close()
        return error("Invalid email or password", 401)

@app.route('/api/historical-data/<line>', methods=['POST', 'OPTIONS'])
def get_historical_data(line):
    if request.method == 'OPTIONS': return handle_options()
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

@app.route('/api/logs', methods=['POST', 'OPTIONS'])
def get_logs():
    if request.method == 'OPTIONS': return handle_options()
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

# -------------------- ENTRY POINT --------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
