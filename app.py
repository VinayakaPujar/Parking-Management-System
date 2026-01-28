from flask import Flask, render_template, jsonify, redirect, url_for, request, flash, session, make_response
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import datetime
import logging

# Optional: import MySQLdb for better exception messages
import MySQLdb

app = Flask(__name__)

# -------------------------
# Configuration
# -------------------------
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'kane@22*')
# Use the correct DB name you created
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'parking_system1')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# Uploads & security
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['ALLOWED_EXTENSIONS'] = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload file size
app.secret_key = os.getenv('SECRET_KEY', 'f894cb67a8c0b040dc8243b0864a320f')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize MySQL
mysql = MySQL(app)

# Logging
logging.basicConfig(level=logging.DEBUG)

# -------------------------
# Helper functions
# -------------------------
def allowed_file(filename):
    """Return True if filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_cursor():
    """Return a cursor or None and log DB errors."""
    try:
        cur = mysql.connection.cursor()
        return cur
    except Exception as e:
        logging.error(f"DB connection error in get_cursor: {e}")
        return None

def test_db_connection():
    cur = get_cursor()
    if not cur:
        return False
    try:
        cur.execute("SELECT 1")
        cur.close()
        return True
    except Exception as e:
        logging.error(f"Database connection failed during test query: {e}")
        return False

# Test DB connection on startup
if not test_db_connection():
    logging.error("Failed to connect to database. Please check your MySQL configuration.")
    print("❌ Database connection failed!")
    print("Please ensure:")
    print("1. MySQL server is running")
    print("2. Database 'parking_system1' exists")
    print("3. User credentials are correct")
    print("4. Run: mysql -u root -p < database_setup.sql")
else:
    print("✅ Database connection successful!")

# -------------------------
# Routes
# -------------------------
@app.route('/')
def index():
    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database cursor not available")
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0] or 0

        cur.execute("SELECT title, message, created_at FROM notifications ORDER BY created_at DESC")
        notifications = cur.fetchall()
        cur.close()
    except Exception as e:
        logging.error(f"Error fetching data for index: {e}")
        user_count = 0
        notifications = []

    return render_template('index.html', user_count=user_count, notifications=notifications)

@app.route('/notification')
def notification():
    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database cursor not available")
        cur.execute("SELECT title, message, created_at FROM notifications ORDER BY created_at DESC")
        notifications = cur.fetchall()
        cur.close()
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        notifications = []

    return render_template('notifications.html', notifications=notifications)

# ===================== ADMIN REGISTRATION =====================
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        mobileNumber = request.form.get('mobileNumber', '').strip()

        if not username or not email or not password or not confirm_password or not mobileNumber:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin_register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin_register'))

        try:
            cur = get_cursor()
            if not cur:
                raise Exception("Database not available")
            
            # Check if username already exists
            cur.execute("SELECT id FROM admins WHERE username=%s", (username,))
            if cur.fetchone():
                flash('Username already exists.', 'danger')
                cur.close()
                return redirect(url_for('admin_register'))

            # Check if email already exists
            cur.execute("SELECT id FROM admins WHERE email=%s", (email,))
            if cur.fetchone():
                flash('Email already exists.', 'danger')
                cur.close()
                return redirect(url_for('admin_register'))

            # Hash the password
            hashed_password = generate_password_hash(password)
            
            cur.execute("INSERT INTO admins (username, email, password, phone) VALUES (%s, %s, %s, %s)", 
                       (username, email, hashed_password, mobileNumber))
            mysql.connection.commit()
            cur.close()
            flash('Admin registered successfully! Please login.', 'success')
            return redirect(url_for('admin_login'))
        except Exception as e:
            logging.error(f"Error during admin registration: {e}")
            flash('Registration error, please try again.', 'danger')

    return render_template('admin_register.html')



# ===================== ADMIN LOGIN =====================
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return redirect(url_for('admin_login'))

        try:
            cur = get_cursor()
            if not cur:
                raise Exception("Database not available")
            
            # Get admin by email
            cur.execute("SELECT id, username, email, password, role FROM admins WHERE email=%s", (email,))
            admin = cur.fetchone()
            cur.close()
            
            if admin and check_password_hash(admin[3], password):  # admin[3] is password
                session['is_admin'] = True
                session['admin_id'] = admin[0]  # admin[0] is id
                session['admin_username'] = admin[1]  # admin[1] is username
                session['admin_email'] = admin[2]  # admin[2] is email
                session['admin_role'] = admin[4]  # admin[4] is role
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            logging.error(f"Error during admin login: {e}")
            flash('Login error, please try again.', 'danger')
            
    return render_template('admin_login.html')


# ===================== ADMIN DASHBOARD =====================
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
            
        # Get parking slot statistics
        cur.execute("SELECT COUNT(*) FROM ParkingSlot WHERE status='available'")
        available_slots = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COUNT(*) FROM ParkingSlot WHERE status='booked'")
        booked_slots = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COUNT(*) FROM ParkingSlot WHERE status='maintenance'")
        maintenance_slots = cur.fetchone()[0] or 0
        
        # Get user statistics
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0] or 0
        
        # Get payment statistics
        cur.execute("SELECT COUNT(*) FROM payments WHERE payment_status='completed'")
        completed_payments = cur.fetchone()[0] or 0
        
        cur.execute("SELECT SUM(amount) FROM payments WHERE payment_status='completed'")
        total_revenue = cur.fetchone()[0] or 0
        
        cur.close()

        return render_template('admin_dashboard.html',
                               available_slots=available_slots,
                               booked_slots=booked_slots,
                               maintenance_slots=maintenance_slots,
                               total_users=total_users,
                               completed_payments=completed_payments,
                               total_revenue=total_revenue,
                               admin_username=session.get('admin_username'))
    except Exception as e:
        logging.error(f"Error loading admin dashboard: {e}")
        flash('Error loading dashboard data.', 'danger')
        return render_template('admin_dashboard.html',
                               available_slots=0,
                               booked_slots=0,
                               maintenance_slots=0,
                               total_users=0,
                               completed_payments=0,
                               total_revenue=0,
                               admin_username=session.get('admin_username'))


# ===================== ADMIN MANAGE SLOTS =====================
@app.route('/admin_manage_slots', methods=['GET', 'POST'])
def admin_manage_slots():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")

        if request.method == 'POST':
            location = request.form.get('location', '').strip()
            slot_number = request.form.get('slot_number', '').strip()
            status = request.form.get('status', 'available')

            if location and slot_number:
                # Check if slot already exists
                cur.execute("SELECT id FROM ParkingSlot WHERE location=%s AND slot_number=%s", (location, slot_number))
                if cur.fetchone():
                    flash('Slot already exists at this location and number.', 'danger')
                else:
                    cur.execute("""
                        INSERT INTO ParkingSlot (location, slot_number, status)
                        VALUES (%s, %s, %s)
                    """, (location, slot_number, status))
                    mysql.connection.commit()
                    flash('New slot added successfully!', 'success')
            else:
                flash('Please fill all required fields.', 'danger')

        # Get all slots with user information
        cur.execute("""
            SELECT ps.id, ps.location, ps.slot_number, ps.status, 
                   u.username, ps.created_at
            FROM ParkingSlot ps
            LEFT JOIN users u ON ps.user_id = u.id
            ORDER BY ps.location, ps.slot_number
        """)
        slots = cur.fetchall()
        cur.close()

    except Exception as e:
        logging.error(f"Error managing slots: {e}")
        slots = []
        flash('Error loading slots.', 'danger')

    return render_template('admin_manage_slots.html', slots=slots)


# ===================== EDIT SLOT =====================
@app.route('/admin_edit_slot/<int:slot_id>', methods=['POST'])
def admin_edit_slot(slot_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    status = request.form.get('status', 'available')
    try:
        cur = get_cursor()
        cur.execute("UPDATE ParkingSlot SET status=%s WHERE id=%s", (status, slot_id))
        mysql.connection.commit()
        cur.close()
        flash('Slot updated successfully!', 'success')
    except Exception as e:
        logging.error(f"Error editing slot: {e}")
        flash('Error updating slot.', 'danger')

    return redirect(url_for('admin_manage_slots'))


# ===================== DELETE SLOT =====================
@app.route('/admin_delete_slot/<int:slot_id>', methods=['POST'])
def admin_delete_slot(slot_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        cur.execute("DELETE FROM ParkingSlot WHERE id=%s", (slot_id,))
        mysql.connection.commit()
        cur.close()
        flash('Slot deleted successfully!', 'success')
    except Exception as e:
        logging.error(f"Error deleting slot: {e}")
        flash('Error deleting slot.', 'danger')

    return redirect(url_for('admin_manage_slots'))


# ===================== ADMIN MANAGE USERS =====================
@app.route('/admin_manage_users')
def admin_manage_users():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
            
        cur.execute("""
            SELECT id, username, email, phone, created_at, 
                   (SELECT COUNT(*) FROM ParkingSlot WHERE user_id = users.id AND status = 'booked') as active_bookings
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cur.fetchall()
        cur.close()
        
    except Exception as e:
        logging.error(f"Error loading users: {e}")
        users = []
        flash('Error loading users.', 'danger')

    return render_template('admin_manage_users.html', users=users)

# ===================== ADMIN MANAGE PAYMENTS =====================
@app.route('/admin_manage_payments')
def admin_manage_payments():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
            
        cur.execute("""
            SELECT p.id, p.plot_no, p.vehicle_no, p.vehicle_type, p.hours, p.amount, 
                   p.payment_type, p.payment_status, p.created_at, u.username
            FROM payments p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
        """)
        payments = cur.fetchall()
        cur.close()
        
    except Exception as e:
        logging.error(f"Error loading payments: {e}")
        payments = []
        flash('Error loading payments.', 'danger')

    return render_template('admin_manage_payments.html', payments=payments)

# ===================== ADMIN MANAGE NOTIFICATIONS =====================
@app.route('/admin_manage_notifications', methods=['GET', 'POST'])
def admin_manage_notifications():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            notification_type = request.form.get('type', 'info')

            if title and message:
                cur.execute("""
                    INSERT INTO notifications (title, message, type)
                    VALUES (%s, %s, %s)
                """, (title, message, notification_type))
                mysql.connection.commit()
                flash('Notification added successfully!', 'success')
            else:
                flash('Please fill all required fields.', 'danger')

        cur.execute("SELECT id, title, message, type, is_active, created_at FROM notifications ORDER BY created_at DESC")
        notifications = cur.fetchall()
        cur.close()

    except Exception as e:
        logging.error(f"Error managing notifications: {e}")
        notifications = []
        flash('Error loading notifications.', 'danger')

    return render_template('admin_manage_notifications.html', notifications=notifications)

# ===================== ADMIN TOGGLE NOTIFICATION =====================
@app.route('/admin_toggle_notification/<int:notification_id>', methods=['POST'])
def admin_toggle_notification(notification_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
            
        cur.execute("UPDATE notifications SET is_active = NOT is_active WHERE id = %s", (notification_id,))
        mysql.connection.commit()
        cur.close()
        flash('Notification status updated successfully!', 'success')
    except Exception as e:
        logging.error(f"Error toggling notification: {e}")
        flash('Error updating notification status.', 'danger')

    return redirect(url_for('admin_manage_notifications'))

# ===================== ADMIN DELETE NOTIFICATION =====================
@app.route('/admin_delete_notification/<int:notification_id>', methods=['POST'])
def admin_delete_notification(notification_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
            
        cur.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
        mysql.connection.commit()
        cur.close()
        flash('Notification deleted successfully!', 'success')
    except Exception as e:
        logging.error(f"Error deleting notification: {e}")
        flash('Error deleting notification.', 'danger')

    return redirect(url_for('admin_manage_notifications'))

# ===================== LOGOUT =====================
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))
# Admin add features
@app.route('/admin_add_features', methods=['GET', 'POST'])
def admin_add_features():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('content', '').strip()
        icon = request.form.get('icon', '🚗')

        if not title or not description:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('admin_add_features'))

        try:
            cur = get_cursor()
            if not cur:
                raise Exception("Database not available")
            cur.execute("INSERT INTO features (title, description, icon) VALUES (%s, %s, %s)",
                        (title, description, icon))
            mysql.connection.commit()
            cur.close()
            flash('Feature content added successfully!', 'success')
            return redirect(url_for('admin_add_features'))
        except Exception as e:
            logging.error(f"Error adding feature content: {e}")
            flash('An error occurred while adding feature content. Please try again.', 'danger')
    return render_template('admin_add_features.html')

# Admin add guidelines
@app.route('/admin_add_guidelines', methods=['GET', 'POST'])
def admin_add_guidelines():
    if not session.get('is_admin'):
        flash('Please log in as admin to access this page.', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'general').strip()
        
        if not title or not content:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('admin_add_guidelines'))
            
        try:
            cur = get_cursor()
            if not cur:
                raise Exception("Database not available")
            cur.execute("INSERT INTO guidelines (title, content, category) VALUES (%s, %s, %s)",
                        (title, content, category))
            mysql.connection.commit()
            cur.close()
            flash('Guideline content added successfully!', 'success')
            return redirect(url_for('admin_add_guidelines'))
        except Exception as e:
            logging.error(f"Error adding guideline content: {e}")
            flash('An error occurred while adding guideline content. Please try again.', 'danger')
    return render_template('admin_add_guidelines.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('mobileNumber', '').strip()

        if not username or not email or not password:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        avatar = None
        if 'avatarUpload' in request.files:
            avatar_file = request.files['avatarUpload']
            if avatar_file and allowed_file(avatar_file.filename):
                filename = secure_filename(avatar_file.filename)
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar_file.save(avatar_path)
                avatar = filename

        try:
            cur = get_cursor()
            if not cur:
                raise Exception("Database not available")
            cur.execute('INSERT INTO users (username, email, password, phone, profile_picture) VALUES (%s, %s, %s, %s, %s)',
                        (username, email, hashed_password, phone, avatar))
            mysql.connection.commit()
            user_id = cur.lastrowid
            cur.close()
            flash('Registration successful!', 'success')
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('webpage'))
        except MySQLdb.Error as e:
            logging.error(f"MySQL Error during registration: {e}")
            flash('Registration failed: Email or username might already exist.', 'danger')
            return redirect(url_for('register'))
        except Exception as e:
            logging.error(f"Error during registration: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        try:
            cur = get_cursor()
            if not cur:
                raise Exception("Database connection or cursor not available")

            # Check if users table exists
            cur.execute("SHOW TABLES LIKE 'users'")
            if not cur.fetchone():
                logging.error("Table 'users' does not exist in database.")
                flash("Database table 'users' is missing.", 'danger')
                return redirect(url_for('login'))

            # Fetch user
            cur.execute("SELECT id, username, email, password FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()

            if user is None:
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

            stored_hash = user[3]
            if not check_password_hash(stored_hash, password):
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

            # Success
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = False
            flash('Login successful!', 'success')
            logging.info(f"User {user[1]} logged in successfully.")
            return redirect(url_for('webpage'))

        except MySQLdb.Error as e:
            logging.error(f"MySQL Error during login: {e}")
            flash(f"MySQL error: {e}", 'danger')  # Show actual DB error for debugging
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash(f"Error: {e}", 'danger')  # Show actual Python error for debugging
            return redirect(url_for('login'))

    return render_template('login.html')


# Webpage after login
@app.route('/webpage')
def webpage():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    logging.info(f"Rendering webpage for user {session.get('username')}")
    return render_template('webpage.html', username=session.get('username'))

# Features page
@app.route('/features')
def features():
    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
        cur.execute("SELECT title, description, icon FROM features WHERE is_active = TRUE")
        features_content = cur.fetchall()
        cur.close()
    except Exception as e:
        logging.error(f"Error fetching features content: {e}")
        features_content = []
    return render_template('features.html', features_content=features_content)

# Guidelines page
@app.route('/guidelines')
def guidelines():
    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
        cur.execute("SELECT title, content, category FROM guidelines WHERE is_active = TRUE")
        guidelines_content = cur.fetchall()
        cur.close()
    except Exception as e:
        logging.error(f"Error fetching guidelines content: {e}")
        guidelines_content = []
    return render_template('guidelines.html', guidelines_content=guidelines_content)

# Contact
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Logout

# Pricing pages
@app.route('/pricing1')
def pricing1():
    return render_template('pricing1.html')

@app.route('/pricing2')
def pricing2():
    return render_template('pricing2.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# Display slots for a location
@app.route('/slots/<location>')
def slots(location):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
        cur.execute("SELECT id, location, slot_number, status FROM ParkingSlot WHERE location = %s", (location,))
        slots = cur.fetchall()
        cur.close()

        # Convert to list so we can append placeholders
        slots = list(slots)

        if len(slots) < 20:
            for i in range(len(slots), 20):
                # placeholder rows: id=None, location, slot_number, status
                slots.append((None, location, i + 1, 'available'))

        return render_template('slots.html', location=location, slots=slots)
    except Exception as e:
        logging.error(f"Error fetching slots for location '{location}': {e}")
        flash('An error occurred while fetching slots. Please try again.', 'danger')
        return redirect(url_for('index'))

# Book a slot
@app.route('/book_slot', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        flash('Please log in to book a slot.', 'danger')
        return redirect(url_for('login'))

    slot_id = request.form.get('slot_id')
    slot_number = request.form.get('slot_number')
    location = request.form.get('location')
    user_id = session.get('user_id')

    if not slot_number or not location:
        flash('Missing slot information.', 'danger')
        return redirect(url_for('index'))

    try:
        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")
        cur.execute("""
            UPDATE ParkingSlot
            SET status = 'booked', user_id = %s, slot_number = %s
            WHERE id = %s AND location = %s AND status = 'available'
        """, (user_id, slot_number, slot_id, location))
        mysql.connection.commit()

        if cur.rowcount == 0:
            flash('Slot is already booked or unavailable.', 'danger')
            cur.close()
            return redirect(url_for('slots', location=location))
        else:
            flash('Slot booked successfully!', 'success')
            cur.close()
            return redirect(url_for('payment', slotNumber=slot_number))
    except Exception as e:
        logging.error(f"Error booking slot: {e}")
        flash('An error occurred while booking the slot. Please try again.', 'danger')
        return redirect(url_for('slots', location=location))

# Payment page
@app.route('/payment')
def payment():
    slotNumber = request.args.get('slotNumber')
    return render_template('payment.html', slotNumber=slotNumber)

# Process payment
@app.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        plot_no = request.form.get('plotNo')
        vehicle_no = request.form.get('vehicleNo')
        vehicle_type = request.form.get('vehicleType')
        hours = int(request.form.get('hours', 0))
        # allow decimals as amount in case
        amount = float(request.form.get('amount', 0))
        payment_type = request.form.get('paymentType')
        user_id = session.get('user_id')

        if not all([plot_no, vehicle_no, vehicle_type, hours, amount, payment_type]):
            return jsonify({'error': 'All fields are required!'}), 400

        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")

        cur.execute("""
            INSERT INTO payments (user_id, plot_no, vehicle_no, vehicle_type, hours, amount, payment_type, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, plot_no, vehicle_no, vehicle_type, hours, amount, payment_type, 'completed'))
        mysql.connection.commit()
        payment_id = cur.lastrowid
        cur.close()

        return jsonify({'message': 'Payment processed successfully!', 'payment_id': payment_id, 'plot_no': plot_no, 'amount': amount, 'date': str(datetime.date.today())}), 200

    except Exception as e:
        logging.error(f"Error processing payment: {e}")
        return jsonify({'error': str(e)}), 500

# Calculate amount
@app.route('/calculate_amount', methods=['POST'])
def calculate_amount():
    try:
        data = request.get_json() or {}
        vehicle_type = data.get('vehicleType')
        hours = int(data.get('hours', 0))

        if vehicle_type not in ['2wheeler', '4wheeler']:
            return jsonify({'error': 'Invalid vehicle type!'}), 400

        if hours <= 0:
            return jsonify({'error': 'Invalid hours!'}), 400

        if vehicle_type == '2wheeler':
            amount = 20 if hours <= 2 else 20 + (hours - 2) * 10
        else:  # 4wheeler
            amount = 40 if hours <= 2 else 40 + (hours - 2) * 20

        return jsonify({'amount': amount}), 200

    except Exception as e:
        logging.error(f"Error calculating amount: {e}")
        return jsonify({'error': str(e)}), 500

# Generate bill & optionally PDF
@app.route('/generate_bill', methods=['GET', 'POST'])
def generate_bill():
    try:
        payment_id = request.args.get('paymentId') if request.method == 'GET' else request.form.get('paymentId')
        if not payment_id:
            return jsonify({'error': 'Payment ID is required'}), 400

        cur = get_cursor()
        if not cur:
            raise Exception("Database not available")

        cur.execute("""
            SELECT p.id, p.plot_no, p.vehicle_no, p.vehicle_type, p.hours, p.amount, p.payment_type, p.created_at, u.username
            FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s
        """, (payment_id,))
        payment_data = cur.fetchone()
        cur.close()

        if not payment_data:
            return jsonify({'error': 'Payment not found'}), 404

        # Unpack the fetched row
        (p_id, plot_no, vehicle_no, vehicle_type, hours, amount, payment_type, created_at, username) = payment_data

        bill_id = f"BILL-{int(p_id):06d}"
        payment_date = created_at.strftime("%Y-%m-%d") if created_at else datetime.date.today().strftime("%Y-%m-%d")
        payment_time = created_at.strftime("%H:%M:%S") if created_at else datetime.datetime.now().strftime("%H:%M:%S")

        rendered = render_template('bill.html',
                                   bill_id=bill_id,
                                   payment_id=p_id,
                                   slot_id=plot_no,
                                   amount=amount,
                                   date=payment_date,
                                   time=payment_time,
                                   username=username,
                                   vehicle_no=vehicle_no,
                                   vehicle_type=vehicle_type,
                                   hours=hours,
                                   payment_type=payment_type)

        # Try to create PDF if possible
        try:
            import pdfkit
            wk_paths = [
                '/usr/local/bin/wkhtmltopdf',
                '/usr/bin/wkhtmltopdf',
                'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe',
                os.getenv('WKHTMLTOPDF_PATH', '')
            ]
            config = None
            for path in wk_paths:
                if path and os.path.isfile(path):
                    config = pdfkit.configuration(wkhtmltopdf=path)
                    break

            options = {
                'page-size': 'A4',
                'encoding': 'UTF-8',
            }

            if config:
                pdf_content = pdfkit.from_string(rendered, False, configuration=config, options=options)
                response = make_response(pdf_content)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=bill_{p_id}.pdf'
                return response
            else:
                logging.warning("wkhtmltopdf not found; returning HTML bill")
                return rendered
        except ImportError:
            logging.warning("pdfkit not installed; returning HTML bill")
            return rendered
        except Exception as pdf_err:
            logging.error(f"PDF generation error: {pdf_err}")
            return rendered

    except Exception as e:
        logging.error(f"Error generating bill: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
