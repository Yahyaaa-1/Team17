import mysql.connector
from config import Config

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        print("Database connection successful")  # Debug print
        return connection
    except Exception as e:
        print(f"Database connection error: {str(e)}")  # Debug print
        return None

def close_connection(connection):
    if connection:
        connection.close()