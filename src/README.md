Rakusens Dashboard
A simple guide to set up the RAKUSENS Dashboard API using Python (Flask) and MySQL.

Team 17 - 
Yahya Ashfak - 23011246

Prerequisites
XAMPP (for MySQL service)
Python 3.11 (or above)
All project files from the OneDrive shared folder (check your email for "Website - Test" files)
Setup Instructions
1. Start MySQL Service in XAMPP
Ensure XAMPP is installed.
Open the XAMPP Control Panel.
Start the MySQL service.
2. Navigate to the API Folder
Open Command Prompt (cmd) and switch to the API folder in your project:

CODE:
cd path\to\your\Website-Test\api
3. Create and Activate a Virtual Environment
Create a virtual environment:

CODE:
python -m venv venv

Activate the virtual environment:

CODE:

venv\Scripts\activate.bat

After successful activation, you should see (venv) at the start of your command line.

4. Install Required Packages
Install the required Python packages using:

CODE:

pip install -r requirements.txt

5. Start the Flask API
Run the Flask application:

CODE:

python app.py

If successful, you should see a message indicating the server is running on port 5000.

Testing
Open these links in your web browser:

Check if the API is running: http://localhost:5000/
Test Database Connection: http://localhost:5000/api/test
Important Notes
Keep XAMPP MySQL running.
Keep the Command Prompt window (with the virtual environment activated) open.
To stop the server, press Ctrl + C in the Command Prompt.
To close the virtual environment, type deactivate and press Enter.
Troubleshooting
If the database connection fails:

Make sure XAMPP MySQL is running.
Check your .env file settings (e.g., database credentials, host, and port).
To restart the API:

Press Ctrl + C to stop the server.
Run python app.py again.
