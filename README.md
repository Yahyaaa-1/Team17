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

3. Create and Activate a Virtual Environment
Create a virtual environment:

python -m venv venv

Activate the virtual environment:

venv\Scripts\activate.bat

4. Install Required Packages

pip install -r requirements.txt

5. Start the Flask API
Run the Flask application:

python app.py
