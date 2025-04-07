from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import mysql.connector
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import time
import threading

class DatabaseManager:
    def __init__(self):
        self.config = Config
    
    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.config.DB_HOST,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME
            )
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

class LogService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def log_event(self, message, type='INFO', log_level='admin'):
        try:
            connection = self.db_manager.get_connection()
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

class AuthService:
    def __init__(self, db_manager, log_service):
        self.db_manager = db_manager
        self.log_service = log_service
    
    def register(self, data):
        full_name, email, new_password = data.get('full_name'), data.get('email'), data.get('new_password')
        if not all([full_name, email, new_password]): 
            return {"success": False, "error": "Missing fields", "code": 400}
        
        conn = self.db_manager.get_connection()
        if not conn: 
            return {"success": False, "error": "DB connection failed", "code": 500}
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts WHERE email = %s", (email,))
        if cursor.fetchone(): 
            return {"success": False, "error": "User already exists", "code": 400}
        
        hashed_pw = generate_password_hash(new_password)
        cursor.execute("""
            INSERT INTO user_accounts (email, full_name, password, admin, active, dark_mode)
            VALUES (%s, %s, %s, 0, 0, 0)
        """, (email, full_name, hashed_pw))
        conn.commit()
        cursor.close()
        conn.close()
        
        self.log_service.log_event(f"New user registered: {email}")
        return {"success": True, "message": "Registration successful"}

    def login(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {"success": False, "error": "Email and password required", "code": 400}

        conn = self.db_manager.get_connection()
        if not conn:
            return {"success": False, "error": "Database connection failed", "code": 500}

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_accounts WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            cursor.close()
            conn.close()
            self.log_service.log_event(f"User logged in: {email}")
            return {
                "success": True,
                'message': 'Login successful',
                'active': True,
                'operator_id': user['operator_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'dark_mode': user['dark_mode'],
                'is_admin': user['admin']
            }
        else:
            cursor.close()
            conn.close()
            return {"success": False, "error": "Invalid email or password", "code": 401}

    def update_password(self, data):
        operator_id = data.get('operator_id')
        new_password = data.get('new_password')

        if not operator_id or not new_password:
            return {"success": False, "error": "Missing parameters", "code": 400}

        if len(new_password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters", "code": 400}

        hashed_pw = generate_password_hash(new_password)

        connection = self.db_manager.get_connection()
        if not connection:
            return {"success": False, "error": "Database connection failed", "code": 500}

        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE user_accounts 
                SET password = %s 
                WHERE operator_id = %s
            """, (hashed_pw, operator_id))
            connection.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

    def update_dark_mode(self, data):
        operator_id = data.get('operator_id')
        dark_mode = data.get('dark_mode', 0)

        if not operator_id:
            return {"success": False, "error": "Missing operator ID", "code": 400}

        connection = self.db_manager.get_connection()
        if not connection:
            return {"success": False, "error": "Database connection failed", "code": 500}

        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE user_accounts
                SET dark_mode = %s
                WHERE operator_id = %s
            """, (dark_mode, operator_id))
            connection.commit()
            self.log_service.log_event(f"Dark mode preference updated for user {operator_id} to {dark_mode}")
            return {"success": True, "message": "Dark mode preference updated"}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

class AdminService:
    def __init__(self, db_manager, log_service):
        self.db_manager = db_manager
        self.log_service = log_service
    
    def validate_admin_request(self, data):
        if not data:
            return {"success": False, "error": "No data received", "code": 400}

        operator_id = data.get('operator_id')
        admin_id = data.get('admin_ID')

        if not operator_id:
            return {"success": False, "error": "Missing operator ID", "code": 400}

        return None, operator_id, admin_id

    def get_user_accounts(self):
        try:
            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user_accounts")
            user_accounts = cursor.fetchall()

            for account in user_accounts:
                if 'created_at' in account and account['created_at']:
                    account['created_at'] = account['created_at'].strftime("%Y-%m-%d %H:%M:%S")

            self.log_service.log_event("Admin retrieved all user accounts", type='INFO', log_level='admin')
            return {
                "success": True, 
                "message": "Retrieved user accounts successfully", 
                "user_accounts": user_accounts
            }
        except Exception as e:
            self.log_service.log_event(f"Error in get_user_accounts: {str(e)}", type='ERROR', log_level='admin')
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

    def toggle_admin_status(self, data):
        try:
            validation_error, operator_id, admin_id = self.validate_admin_request(data)
            if validation_error:
                return validation_error

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT admin FROM user_accounts WHERE operator_id = %s", (operator_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": "User not found", "code": 404}

            current_status = int(user['admin'])
            new_status = 1 if current_status == 0 else 0

            cursor.execute("""
                UPDATE user_accounts
                SET admin = %s
                WHERE operator_id = %s
            """, (new_status, operator_id))
            connection.commit()

            self.log_service.log_event(
                f"User {operator_id} Admin status changed to {new_status} by Admin - {admin_id}", 
                type='INFO', 
                log_level='admin'
            )

            return {
                "success": True,
                "message": f'User admin status updated to {"admin" if new_status == 1 else "operator"}',
                "admin": new_status
            }
        except Exception as e:
            self.log_service.log_event(f"Error in toggle_admin_status: {str(e)}", type='ERROR', log_level='admin')
            return {"success": False, "error": str(e), "code": 400}

    def toggle_user_status(self, data):
        try:
            validation_error, operator_id, admin_id = self.validate_admin_request(data)
            if validation_error:
                return validation_error

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT active, email FROM user_accounts WHERE operator_id = %s", (operator_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": "User not found", "code": 404}

            new_status = 0 if int(user['active']) == 1 else 1
            cursor.execute("""
                UPDATE user_accounts
                SET active = %s
                WHERE operator_id = %s
            """, (new_status, operator_id))
            connection.commit()

            status_text = "active" if new_status == 1 else "inactive"
            self.log_service.log_event(
                f"User {user['email']} (ID: {operator_id}) status changed to {status_text}", 
                type='INFO', 
                log_level='admin'
            )

            return {
                "success": True,
                "message": f'User status updated to {status_text}',
                "new_status": new_status
            }
        except Exception as e:
            self.log_service.log_event(f"Error in toggle_user_status: {str(e)}", type='ERROR', log_level='admin')
            return {"success": False, "error": str(e), "code": 500}

    def delete_user(self, data):
        try:
            validation_error, operator_id, admin_id = self.validate_admin_request(data)
            if validation_error:
                return validation_error

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT operator_id, email FROM user_accounts WHERE operator_id = %s", (operator_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": f'User {operator_id} not found', "code": 404}

            cursor.execute("DELETE FROM user_accounts WHERE operator_id = %s", (operator_id,))
            affected_rows = cursor.rowcount
            connection.commit()

            if affected_rows > 0:
                self.log_service.log_event(
                    f"User {operator_id} deleted by admin {admin_id}", 
                    type='WARNING', 
                    log_level='admin'
                )
                return {
                    "success": True,
                    "message": f'User {operator_id} has been deleted',
                    "rows_affected": affected_rows
                }
            else:
                return {"success": False, "error": "Delete operation failed", "code": 500}
        except Exception as e:
            self.log_service.log_event(f"Error in delete_user: {str(e)}", type='ERROR', log_level='admin')
            return {"success": False, "error": str(e), "code": 500}

    def delete_sensor(self, data):
        try:
            sensor = data.get('sensorName')
            table_id = data.get('tableID')

            if not sensor:
                return {"success": False, "error": "Missing Sensor Name", "code": 400}
            if not table_id:
                return {"success": False, "error": "Missing Table ID", "code": 400}

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SHOW COLUMNS FROM {table_id} LIKE %s", (sensor,))
            column_exists = cursor.fetchone()
            
            if not column_exists:
                return {"success": False, "error": f'Sensor {sensor} does not exist in the table', "code": 400}

            cursor.execute(f"ALTER TABLE {table_id} DROP COLUMN {sensor}")
            connection.commit()
            
            self.log_service.log_event(
                f"Sensor {sensor} deleted from table {table_id}", 
                type='WARNING', 
                log_level='admin'
            )

            return {"success": True, "message": f'Sensor {sensor} deleted from {table_id}'}
        except Exception as e:
            self.log_service.log_event(f"Error in delete_sensor: {str(e)}", type='ERROR', log_level='admin')
            return {"success": False, "error": str(e), "code": 400}

    def update_user_details(self, data):
        try:
            operator_id = data.get('operator_id')
            new_email = data.get('Nemail')
            new_fullname = data.get('Nfullname')

            missing_fields = []
            if not operator_id: missing_fields.append('Operator ID')
            if not new_email: missing_fields.append('Email')
            if not new_fullname: missing_fields.append('Full Name')

            if missing_fields:
                return {"success": False, "error": f'Missing fields: {", ".join(missing_fields)}', "code": 400}

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT email, full_name FROM user_accounts WHERE operator_id = %s", (operator_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": "User not found", "code": 404}

            cursor.execute("SELECT operator_id FROM user_accounts WHERE email = %s AND operator_id != %s", 
                         (new_email, operator_id))
            if cursor.fetchone():
                return {"success": False, "error": "Email already in use by another user", "code": 400}

            cursor.execute("""
                UPDATE user_accounts
                SET email = %s, full_name = %s
                WHERE operator_id = %s
            """, (new_email, new_fullname, operator_id))
            connection.commit()

            self.log_service.log_event(
                f"User details updated - ID: {operator_id}, "
                f"Email: {user['email']} -> {new_email}, "
                f"Name: {user['full_name']} -> {new_fullname}",
                type='INFO',
                log_level='admin'
            )

            return {"success": True, "message": "User details updated successfully"}
        except Exception as e:
            self.log_service.log_event(f"Error in update_user_details: {str(e)}", type='ERROR', log_level='admin')
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

    def get_table_headers(self, table_id):
        try:
            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor()
            cursor.execute(f"SHOW COLUMNS FROM {table_id}")
            columns = cursor.fetchall()
            headers = [column[0] for column in columns]
            return {"success": True, "headers": headers}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 400}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

class DataService:
    def __init__(self, db_manager, log_service):
        self.db_manager = db_manager
        self.log_service = log_service
    
    def get_historical_data(self, line, data):
        try:
            length = int(data.get("length", 50))
            search_value = data.get("searchValue", "")
            date_filter = data.get("dateFilter", "")

            query = f"SELECT * FROM {line} WHERE 1=1"
            if date_filter:
                query += f" AND DATE(timestamp) = '{date_filter}'"
            if search_value:
                query += f" AND (timestamp LIKE '%{search_value}%')"
            query += f" ORDER BY timestamp DESC LIMIT {length}"

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            for record in results:
                record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            
            return {"success": True, "data": results}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

    def get_logs(self):
        try:
            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100")
            results = cursor.fetchall()
            for record in results:
                record["timestamp"] = record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "data": results}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

    def get_live_data(self, line):
        try:
            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            query = f"SELECT * FROM {line} ORDER BY timestamp DESC LIMIT 1"
            cursor.execute(query)
            data = cursor.fetchone()
            if not data:
                return {"success": False, "error": "No live data available", "code": 404}
            
            data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'connection' in locals(): connection.close()

    def get_forecasted_data(self, line):
        try:
            valid_lines = ["line4", "line5"]
            if line not in valid_lines:
                return {"success": False, "error": "Invalid line selected", "code": 400}

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            query = f"SELECT * FROM forecasted{line} ORDER BY forecast_time ASC"
            cursor.execute(query)
            data = cursor.fetchall()
            if not data:
                return {"success": False, "error": "No forecasted data available", "code": 404}

            formatted_data = [
                {
                    **record,
                    'forecast_time': record['forecast_time'].strftime("%Y-%m-%d %H:%M:%S")
                } for record in data
            ]
            self.log_service.log_event(f"Forecasted data retrieved for {line}", type='INFO')
            return {"success": True, "data": formatted_data}
        except Exception as e:
            self.log_service.log_event(f"Error in forecast data: {str(e)}", type='ERROR')
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

    def get_historical_data_sensor(self, line, sensor, args):
        try:
            length = args.get('length', default=50, type=int)
            search_value = args.get('searchValue', default='', type=str)
            date_filter = args.get('dateFilter', default='', type=str)
            start_date_time = args.get('startDateTime', default='', type=str)
            end_date_time = args.get('endDateTime', default='', type=str)

            query = f"SELECT timestamp, {sensor} as value FROM {line} WHERE 1=1"
            if date_filter:
                query += f" AND DATE(timestamp) = '{date_filter}'"
            if start_date_time and end_date_time:
                query += f" AND timestamp BETWEEN '{start_date_time}' AND '{end_date_time}'"
            if search_value:
                query += f" AND (timestamp LIKE '%{search_value}%')"
            query += f" ORDER BY timestamp DESC LIMIT {length}"

            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            data = cursor.fetchall()
            formatted = [
                {
                    'timestamp': record['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    'value': float(record['value'])
                } for record in data
            ]
            return {"success": True, "data": formatted}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'connection' in locals(): connection.close()

    def get_sensor_data(self, line, sensor):
        try:
            connection = self.db_manager.get_connection()
            if not connection:
                return {"success": False, "error": "Database connection failed", "code": 500}

            cursor = connection.cursor(dictionary=True)
            query = f"SELECT timestamp, {sensor} FROM {line} ORDER BY timestamp DESC LIMIT 1"
            cursor.execute(query)
            data = cursor.fetchone()
            if not data:
                return {"success": False, "error": "No data available for this sensor", "code": 404}
            
            data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e), "code": 500}
        finally:
            if 'connection' in locals(): connection.close()

class SimulationService:
    def __init__(self, db_manager, log_service):
        self.db_manager = db_manager
        self.log_service = log_service
        self.thread = None 
        self.LINE_4_SENSORS = ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08"]
        self.LINE_5_SENSORS = ["r01", "r02", "r03", "r04", "r05", "r06", "r07", "r08", 
                             "r09", "r10", "r11", "r12", "r13", "r14", "r15", "r16", "r17"]
        
        self.SENSOR_RANGES_LINE4 = {
            "r01": {"avg": 129.10, "min": 16.00, "max": 258.00},
            "r02": {"avg": 264.81, "min": 18.00, "max": 526.00},
            "r03": {"avg": 255.77, "min": 17.00, "max": 476.00},
            "r04": {"avg": 309.04, "min": 13.00, "max": 554.00},
            "r05": {"avg": 253.94, "min": 10.00, "max": 440.00},
            "r06": {"avg": 268.39, "min": 8.00, "max": 485.00},
            "r07": {"avg": 263.18, "min": 9.00, "max": 525.00},
            "r08": {"avg": 210.97, "min": 8.00, "max": 434.00}
        }
        
        self.SENSOR_RANGES_LINE5 = {
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
    
    def get_timezone_offset(self):
        current_month = time.localtime().tm_mon
        return "+01" if 4 <= current_month <= 10 else "+00"

    def generate_sensor_reading(self, sensor, ranges):
        avg_temp = ranges[sensor]["avg"]
        fluctuation = avg_temp * 0.02
        new_temp = random.uniform(avg_temp - fluctuation, avg_temp + fluctuation)
        limits = ranges[sensor]
        new_temp = max(limits["min"], min(limits["max"], new_temp))
        return round(new_temp, 2)

    def insert_line_readings(self, cursor, line_number, sensors, ranges, timestamp, timezone):
        values = [timestamp, timezone]
        values.extend([self.generate_sensor_reading(sensor, ranges) for sensor in sensors])

        try:
            query = f"""
            INSERT INTO line{line_number}
            (timestamp, timezone, {', '.join(sensors)})
            VALUES (%s, %s, {', '.join(['%s'] * len(sensors))})
            """
            cursor.execute(query, values)
            readings_dict = dict(zip(sensors, values[2:]))
            print(f"Line {line_number}: {readings_dict}")
        except Exception as e:
            self.log_service.log_event(f"Error inserting line {line_number} data: {str(e)}", type='ERROR')
            print(f"Error inserting line {line_number} data: {e}")
            print("Parameters:", values)
            print("Number of parameters:", len(values))
            raise

    def generate_temperature_readings(self):
        while True:
            connection = None
            cursor = None

            try:
                connection = self.db_manager.get_connection()
                if not connection:
                    raise Exception("Failed to establish database connection")

                cursor = connection.cursor()
                current_timestamp = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
                timezone_offset = self.get_timezone_offset()
                
                self.insert_line_readings(cursor, 4, self.LINE_4_SENSORS, self.SENSOR_RANGES_LINE4, 
                                       current_timestamp, timezone_offset)
                self.insert_line_readings(cursor, 5, self.LINE_5_SENSORS, self.SENSOR_RANGES_LINE5, 
                                       current_timestamp, timezone_offset)
                
                connection.commit()
                self.log_service.log_event("Temperature readings generated successfully", type='INFO')
                time.sleep(30)
                
            except Exception as e:
                self.log_service.log_event(f"Simulation error: {str(e)}", type='ERROR')
                print(f"Simulation error: {e}")
                time.sleep(5)
            finally:
                if cursor: cursor.close()
                if connection: connection.close()
    def start(self):
        """Start the simulation in a separate thread"""
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(
                target=self.generate_temperature_readings,
                daemon=True
            )
            self.thread.start()
            self.log_service.log_event("Temperature simulation started", type='INFO')

    def stop(self):
        """Stop the simulation if needed"""
        # The thread will stop automatically when the application exits
        # because it's a daemon thread
        pass

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, 
            resources={r"/api/*": {"origins": ["null", "http://localhost:*", "http://127.0.0.1:*"]}},
            supports_credentials=True,
            allow_headers=["Content-Type", "Authorization"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        
        
        
        self.db_manager = DatabaseManager()
        self.log_service = LogService(self.db_manager)
        self.auth_service = AuthService(self.db_manager, self.log_service)
        self.admin_service = AdminService(self.db_manager, self.log_service)
        self.data_service = DataService(self.db_manager, self.log_service)
        self.simulation_service = SimulationService(self.db_manager, self.log_service)
        
        self.setup_routes()
    
    def handle_options(self):
        return '', 204
    
    def success(self, msg, **kwargs):
        return jsonify({"success": True, "message": msg, **kwargs})
    
    def error(self, msg, code=400):
        return jsonify({"success": False, "error": msg}), code
    
    def setup_routes(self):
        @self.app.route('/')
        @self.app.route('/home')
        def home():
            return render_template('home.html')

        @self.app.route('/api/log', methods=['POST', 'OPTIONS'])
        def trigger_log():
            if request.method == 'OPTIONS': return self.handle_options()
            data = request.get_json()
            self.log_service.log_event(
                data.get('message'), 
                type=data.get('type', 'INFO'), 
                log_level=data.get('level', 'admin')
            )
            return self.success("Log event triggered")

        @self.app.route('/api/register', methods=['POST', 'OPTIONS'])
        def register():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.auth_service.register(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 400))
            return self.success(result['message'])

        @self.app.route('/api/login', methods=['POST', 'OPTIONS'])
        def login():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.auth_service.login(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 400))
            return jsonify(result)

        @self.app.route('/api/historical-data/<line>', methods=['POST'])
        def get_historical(line):
            result = self.data_service.get_historical_data(line, request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/logs', methods=['POST'])
        def get_logs():
            result = self.data_service.get_logs()
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/live-data/<line>', methods=['GET', 'OPTIONS'])
        def get_live_data(line):
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.data_service.get_live_data(line)
            if not result['success']:
                return self.error(result['error'], result.get('code', result.get('code', 500)))
            return jsonify(result)

        @self.app.route('/api/admin/user-accounts', methods=['GET'])
        def get_user_accounts():
            result = self.admin_service.get_user_accounts()
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/admin/toggle-admin-status', methods=['POST', 'OPTIONS'])
        def toggle_admin_status():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.admin_service.toggle_admin_status(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 400))
            return jsonify(result)

        @self.app.route('/api/admin/toggle-user-admin', methods=['POST', 'OPTIONS'])
        def toggle_user_admin():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.admin_service.toggle_admin_status(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 400))
            return jsonify(result)

        @self.app.route('/api/admin/delete-user', methods=['POST', 'OPTIONS'])
        def delete_user():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.admin_service.delete_user(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/admin/delete-sensor', methods=['POST', 'OPTIONS'])
        def delete_sensor():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.admin_service.delete_sensor(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 400))
            return jsonify(result)

        @self.app.route('/api/admin/toggle-user-status', methods=['POST', 'OPTIONS'])
        def toggle_user_status():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.admin_service.toggle_user_status(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/update-password', methods=['POST', 'OPTIONS'])
        def update_password():
            if request.method == "OPTIONS": return jsonify({"success": True})
            result = self.auth_service.update_password(request.get_json())
            if not result['success']:
                return jsonify({"success": False, "error": result['error']}), result.get('code', 500)
            return
        @self.app.route('/api/admin/update-user-details', methods=['POST', 'OPTIONS'])
        def update_user_details():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.admin_service.update_user_details(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/admin/table-headers', methods=['GET', 'OPTIONS'])
        def get_table_headers():
            if request.method == 'OPTIONS': return self.handle_options()
            table_id = request.args.get('tableID')
            result = self.admin_service.get_table_headers(table_id)
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/historical/<line>/<sensor>', methods=['GET', 'OPTIONS'])
        def get_historical_sensor_data(line, sensor):
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.data_service.get_historical_data_sensor(
                line, 
                sensor, 
                request.args
            )
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/forecasted-data/<line>', methods=['GET', 'OPTIONS'])
        def get_forecasted_data(line):
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.data_service.get_forecasted_data(line)
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)
            

        @self.app.route('/api/sensor-data/<line>/<sensor>', methods=['GET', 'OPTIONS'])
        def get_sensor_data(line, sensor):
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.data_service.get_sensor_data(line, sensor)
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/update-dark-mode', methods=['POST', 'OPTIONS'])
        def update_dark_mode():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.auth_service.update_dark_mode(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

        @self.app.route('/api/forgot-password', methods=['POST', 'OPTIONS'])
        def forgot_password():
            if request.method == 'OPTIONS': return self.handle_options()
            result = self.auth_service.forgot_password(request.get_json())
            if not result['success']:
                return self.error(result['error'], result.get('code', 500))
            return jsonify(result)

    def run(self, host='127.0.0.1', port=5000, debug=True):
        try:
            self.app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False  # Disable reloader when using threads
            )
        except Exception as e:
            self.log_service.log_event(
                f"Application failed to start: {str(e)}", 
                type='ERROR', 
                log_level='admin'
            )

def create_app():
    """Factory function to create and configure the Flask application"""
    return FlaskApp()

if __name__ == '__main__':
    # Create the app first
    app = create_app()
    
    # Create and start simulation thread using the instance's simulation service
    simulation_thread = threading.Thread(
        target=app.simulation_service.generate_temperature_readings,
        daemon=True
    )
    simulation_thread.start()
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True)