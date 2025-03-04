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
    
# Admin Routes
# Get all user accounts
@app.route('/api/admin/user-accounts', methods=['GET', 'OPTIONS'])
def get_user_accounts():
    print(f"Received {request.method} request to retrieve admin details")  # Debug print
    
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
        print(f"Error in retrieving user accounts: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({
            'success': True, 
            'message': 'Retrieved user accounts successfully',
            'user_accounts': user_accounts
        })

# Get all employees
@app.route('/api/admin/employee-reg', methods=['GET', 'OPTIONS'])
def get_employee_reg():
    print(f"Received {request.method} request to retrieve admin details")  # Debug print
    
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
        print(f"Error in retrieving user accounts: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({
            'success': True, 
            'message': 'Retrieved user accounts successfully',
            'employee_registry': employee_registry
        })

# Get user status
@app.route('/api/admin/toggle-user-status', methods=['POST', 'OPTIONS'])
def toggleUserStatus():
    print(f"Received {request.method} request to change user active status")  # Debug print
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
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
        print(f"Error in retrieving user accounts: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 400
    
# Delete user account
@app.route('/api/admin/delete-user', methods=['POST', 'OPTIONS'])
def deleteUser():
    print(f"Received {request.method} request to delete user")  # Debug print
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
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
        print(f"Error in retrieving user accounts: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 400

# Delete employee
@app.route('/api/admin/delete-employee', methods=['POST', 'OPTIONS'])
def deleteEmployee():
    print(f"Received {request.method} request to delete user")  # Debug print
    
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405
        
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
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
        print(f"Error in retrieving user accounts: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 400

# Main
if __name__ == '__main__':
    app.run(debug=Config.DEBUG)