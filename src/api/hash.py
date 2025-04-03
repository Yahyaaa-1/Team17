import mysql.connector
from werkzeug.security import generate_password_hash

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="rakusensdatabase"
)
cursor = conn.cursor()

# Step 1: Empty the employee_registry table
cursor.execute("TRUNCATE TABLE employee_registry;")

# Step 2: Employee data
employees = [
    ("W001", "john.doe@rakusens.co.uk", "John Doe", "TempPass123!"),
    ("W002", "jane.smith@rakusens.co.uk", "Jane Smith", "Welcome456@"),
    ("W004", "emily.brown@rakusens.co.uk", "Emily Brown", "Starter234$"),
    ("W005", "david.lee@rakusens.co.uk", "David Lee", "Newuser567%"),
    ("W006", "sarah.wilson@rakusens.co.uk", "Sarah Wilson", "Temp890&"),
    ("W008", "lisa.martinez@rakusens.co.uk", "Lisa Martinez", "FirstLogin678!"),
    ("W009", "kevin.chen@rakusens.co.uk", "Kevin Chen", "Temporary901@"),
    ("W010", "amanda.taylor@rakusens.co.uk", "Amanda Taylor", "Access234#"),
    ("W011", "christopher.kim@rakusens.co.uk", "Christopher Kim", "Welcome567$"),
    ("W013", "daniel.park@rakusens.co.uk", "Daniel Park", "Starter123&"),
    ("W014", "rachel.wong@rakusens.co.uk", "Rachel Wong", "Newuser456*"),
    ("W015", "thomas.anderson@rakusens.co.uk", "Thomas Anderson", "Initial789!"),
    ("W016", "olivia.nguyen@rakusens.co.uk", "Olivia Nguyen", "FirstLogin012@"),
    ("W017", "ryan.patel@rakusens.co.uk", "Ryan Patel", "Temporary345#"),
    ("W018", "emma.thompson@rakusens.co.uk", "Emma Thompson", "Access678$"),
    ("W019", "brandon.lee@rakusens.co.uk", "Brandon Lee", "Welcome901%"),
]

# Step 3: Insert new employees with hashed passwords
for operator_id, email, full_name, temp_password in employees:
    hashed_password = generate_password_hash(temp_password)
    
    cursor.execute("""
        INSERT INTO employee_registry (operator_id, email, full_name, temp_password)
        VALUES (%s, %s, %s, %s);
    """, (operator_id, email, full_name, hashed_password))

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()

print("Employee registry has been updated successfully!")
