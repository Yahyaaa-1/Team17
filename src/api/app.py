from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from config import Config
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

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
    print(f"Received {request.method} request to register")  # Debug print
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
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
            print(f"Database error: {err}")  # Debug print
            return jsonify({'success': False, 'error': 'Database error occurred'}), 500
        finally:
            cursor.close()
            connection.close()

        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        print(f"Error in register: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 400

# user Login
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    print(f"Received {request.method} request to login")  # Debug print
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        print(f"Received login data: {data}")  # Debug print
        
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
        print(f"Error in login: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500
# Main
if __name__ == '__main__':
    app.run(debug=Config.DEBUG)