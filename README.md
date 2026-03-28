🚗 **Parking Management System**

A web-based parking management system built with Flask, MySQL, and Python. The application supports both User and Admin roles, enabling slot booking, payments, and efficient management of parking spaces with user-friendly dashboards.

✨ **Features**

User Registration & Login: Secure authentication with password hashing and profile picture upload.

Admin Registration & Login: Separate access for admins with dashboard and management tools.

Slot Management: Add, edit, and delete parking slots; track availability and bookings.

Booking: Users can reserve available slots and view location-based options.

Payment & Billing: Dynamic payment calculation (based on vehicle type & hours), with bills generated in HTML and PDF.

Notifications: Admins can create notifications for users.

Features & Guidelines: Admins can add and update system features and guidelines.

Session Management & Security: Session handling, upload restrictions, allowed file types, and error logging.

Extensive Logging: Debug and error logs for troubleshooting.

🛠️ **Technology Stack**

Backend: Python, Flask, Flask-MySQLdb, Werkzeug

Database: MySQL (parking_system1)

Frontend: Flask templates (HTML, CSS, JS)

PDF Generation: Optional via pdfkit + wkhtmltopdf

🚀 **Getting Started**
✅ Prerequisites

Python 3.x

MySQL Server

pip (Python package installer)

🔧 Installation

Clone the repository

git clone https://github.com/VinayakaPujar/parking-system-flask.git
cd parking-system-flask


Install Python dependencies

pip install flask flask-mysqldb werkzeug pdfkit


Create MySQL Database

Start MySQL server.

Run SQL scripts to create database and tables. Example:

CREATE DATABASE parking_system1;
USE parking_system1;
-- Create necessary tables as per app.py requirements


Configure environment variables (optional)

Copy .env.example to .env and set values:

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DB=parking_system1
SECRET_KEY=your-secret-key

▶️**Running the App**
python app.py


The app runs at: http://localhost:5000/


🎯 **Usage**

User: Register, login, view slots, book a slot, make payments, and download bills.

Admin: Register/login, manage slots and payments, add features/guidelines, and view the dashboard.

🔒 **Security Notes**

For production, move all sensitive configuration values to environment variables.

Hash both admin and user passwords.

Use HTTPS and strong secret keys.


**Results**

<img width="1920" height="1080" alt="Screenshot 2025-08-24 223818" src="https://github.com/user-attachments/assets/add28243-aea8-45df-b051-d9c3fa882f02" />




<img width="1920" height="1080" alt="Screenshot 2025-08-24 223833" src="https://github.com/user-attachments/assets/d5563997-6d17-49df-9b21-cf3b7d6fa091" />




<img width="1920" height="1080" alt="Screenshot 2025-08-24 223924" src="https://github.com/user-attachments/assets/bd29c1d0-efa5-411a-bd56-4691ad7761d9" />




<img width="1920" height="1080" alt="Screenshot 2025-08-24 224001" src="https://github.com/user-attachments/assets/2f703479-2cbe-4eb4-90ea-88cdc8a5a32b" />













