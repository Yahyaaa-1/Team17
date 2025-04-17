Rakusen’s Interactive, real-time visualisation dashboard

Yahya Ashfak 23011246

Aadam Ahmed 23018946

Barirah Irfan 23043808

Saiful-Islam-Waheed 23018692

Osman Talib 23017617

Mohammed Ramzan Iqbal 23016117

Harris Khan 23011221

A simple guide to set up the RAKUSENS Dashboard API using Python (Flask) and MySQL.

Prerequisites
XAMPP (for MySQL service)
Python 3.11 (or above)
All project files from the OneDrive shared folder (check your email for "Website - Test" files)
Steps
1. Start MySQL Service in XAMPP
Ensure XAMPP is installed.
Open the XAMPP Control Panel.
Start the MySQL service.
2. Navigate to the API Folder
Open Command Prompt (cmd) and switch to the API folder in your project:

cd path\to\your\Website-Test\api

3. Run machine-learning model (enter a specific future timestamp in the code (located in the api folder) beforehand:
   python machine_learning_aadam.py

4. Create and Activate a Virtual Environment
Create a virtual environment:

python -m venv venv

venv\Scripts\activate.bat

5. Install Required Packages

pip install -r requirements.txt

6. Start the Flask API
Run the Flask application:

python app.py

Testing
Open these links in your web browser:

Check if the API is running:
http://localhost:5000/
Test Database Connection:
http://localhost:5000/api/test
Important Notes
Keep XAMPP MySQL running.
Keep the Command Prompt window (with the virtual environment activated) open.
To stop the server, press Ctrl + C in the Command Prompt.
To close the virtual environment, type deactivate and press Enter.
Troubleshooting
If database connection fails:

Make sure XAMPP MySQL is running.
Check your .env file settings (e.g., database credentials, host, and port).
To restart the API:

Press Ctrl + C to stop the server.
Run python app.py again.

