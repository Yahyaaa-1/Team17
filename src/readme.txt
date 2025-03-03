RAKUSENS DASHBOARD API SETUP GUIDE

HTML Form → JavaScript → Python (Flask) → MySQL
(Frontend)   (Validation   (Backend/API    (Database)
             & API calls)   like PHP)
			  This part is being setup now


BEFORE STARTING:

Make sure XAMPP is installed and running (MySQL service)
Make sure Python 3.11 is installed
Make sure you have all the project files from the OneDrive shared folder, check email (Website - Test
SETUP STEPS:
Open Command Prompt (cmd)

Navigate to api folder:
cd path\to\your\Website-Test\api

Create virtual environment:
python -m venv venv

Activate virtual environment:
venv\Scripts\activate.bat
(You should see (venv) at the start of your command line)

Install required packages:
pip install -r requirements.txt

Start the Flask API:
python app.py
(You should see a message saying the server is running)

TESTING:
Open these links in your web browser:

Check API is running:
http://localhost:5000/

Check database connection:
http://localhost:5000/api/test

IMPORTANT NOTES:
Keep XAMPP MySQL running
Keep Command Prompt window open
To stop server: Press Ctrl+C
To close environment: Type 'deactivate'
TROUBLESHOOTING:
If database connection fails:

Check XAMPP MySQL is running
Check .env file settings
To restart the API:

Press Ctrl+C
Run 'python app.py' again