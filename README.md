# Employee Roster Management System

A complete starter web application for managing weekly employee rosters.

## Requirements
- Python 3.10+
- Visual Studio Code or Visual Studio with Python support
- Internet connection only for installing packages and sending email

## Run
1. Open this folder in Visual Studio / VS Code.
2. Open a terminal in this folder.
3. Create a virtual environment:
   python -m venv .venv
4. Activate it:
   Windows: .venv\Scripts\activate
5. Install dependencies:
   pip install -r requirements.txt
6. Start:
   python app.py
7. Open http://127.0.0.1:5000

Default admin:
Email: admin@roster.local
Password: admin123

Change the password before using this for real employees.

## Features
- Admin login
- Employee management
- Weekly roster creation
- CSV roster upload
- Individual employee roster view
- Dashboard
- SQLite database
- Responsive Bootstrap UI
- Optional email sending through SMTP
- CSV template download

## CSV format
name,email,week_start,monday,tuesday,wednesday,thursday,friday,saturday,sunday
John Doe,john@example.com,2026-08-10,08:00-16:00,OFF,16:00-00:00,08:00-16:00,08:00-16:00,OFF,OFF

For a real deployment, use HTTPS, strong passwords, CSRF protection, production database, and a proper mail provider.
