@echo off
:: Step 2: Navigate to the API folder
cd C:\Users\Yahya\Downloads\github\Team17-10\src\api

:: Step 3: Create a virtual environment
python -m venv venv

:: Step 3.1: Activate the virtual environment
call venv\Scripts\activate.bat

:: Step 4: Install required packages
pip install -r requirements.txt

:: Step 5: Start the Flask API
python app.py

pause
