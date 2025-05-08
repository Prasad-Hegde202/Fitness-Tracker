import smtplib
import os
import random
import time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

# ✅ Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Security Key (Environment variable-based)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key_here_change_me')

# Flask-Mail Configuration (Use environment variables for security)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mdesai9118@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'plzz ralp nzlh flde'  # Use App Password if using Gmail
app.config['MAIL_DEFAULT_SENDER'] = ('Fitex', 'mdesai9118@gmail.com')

# ✅ Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'
    
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.id} - {self.name}>'
    
# Fitness Goals Model
class FitnessGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    steps = db.Column(db.Integer, nullable=False)
    calories = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ Route to Save User Fitness Goal
@app.route('/save_goal', methods=['POST'])
@login_required
def save_goal():
    try:
        data = request.json
        print("📩 Received Data:", data)  # Debugging

        if not data:
            return jsonify({"error": "No data received"}), 400

        new_goal = FitnessGoal(
            user_id=current_user.id,  # Automatically assign logged-in user
            activity=data.get('activity'),
            distance=float(data.get('distance')),
            steps=int(data.get('steps')),
            calories=int(data.get('calories'))
        )

        db.session.add(new_goal)
        db.session.commit()

        return jsonify({"message": "Goal saved successfully!", "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/view_goals', methods=['GET'])
@login_required
def view_goals():
    user_id = request.args.get('user_id')

    if not user_id:
        print("🚨 Missing user_id in request")
        return jsonify({"error": "User ID required"}), 400

    print(f"📢 Fetching goals for User ID: {user_id}")

    goals = FitnessGoal.query.filter_by(user_id=user_id).all()

    if not goals:
        print(f"⚠️ No goals found for User ID: {user_id}")
        return jsonify({"message": "No fitness goals found"}), 404

    goals_data = [
        {
            "activity": goal.activity,
            "distance": goal.distance,
            "steps": goal.steps,
            "calories": goal.calories
        }
        for goal in goals
    ]
    
    print(f"✅ Goals Found: {goals_data}")  # Debug print
    return jsonify(goals_data)


@app.route('/goals')
@login_required
def goals_page():
    return render_template('goals.html')


# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# About Page Route
@app.route('/about')
def about():
    return render_template('about.html')

# Services Page Route
@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('FirstName')
        last_name = request.form.get('LastName')  # ✅ Fixed name
        email = request.form.get('Email')
        phone = request.form.get('PhoneNumber')
        message = request.form.get('Message')  # ✅ Fixed name

        if not all([first_name, last_name, email, phone, message]):
            flash('All fields are required!', 'danger')
        else:
            full_name = f"{first_name} {last_name}"  # Combine first & last name
            new_contact = Contact(name=full_name, email=email, message=message)

            try:
                db.session.add(new_contact)
                db.session.commit()
                flash('Your message has been sent successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving contact: {str(e)}', 'danger')

        return redirect(url_for('contact'))

    return render_template('contact.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already registered. Please log in or use a different email.", "danger")
            return redirect(url_for('signup'))

        # Generate OTP
        otp = random.randint(100000, 999999)
        session['otp'] = otp
        session['otp_time'] = time.time()
        session['user_data'] = {'name': name, 'phone': phone, 'email': email, 'password': password}

        # Send OTP to email
        try:
            msg = Message("Your OTP Code", recipients=[email])
            msg.body = f"Your OTP for registration is {otp}. It will expire in 5 minutes."
            mail.send(msg)
            flash("OTP sent to your email!", "success")
            return redirect(url_for('verify_otp'))
        except smtplib.SMTPException as e:
            flash(f"Error sending email: {str(e)}", "danger")

    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        
        if 'otp' in session and entered_otp and int(entered_otp) == session['otp']:
            user_data = session.pop('user_data', None)
            if user_data:
                hashed_password = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
                new_user = User(
                    name=user_data['name'],
                    phone=user_data['phone'],
                    email=user_data['email'],
                    password=hashed_password
                )
                db.session.add(new_user)
                db.session.commit()

                # Send registration details via email
                try:
                    msg = Message("Registration Successful", recipients=[user_data['email']])
                    msg.body = f"Name: {user_data['name']}\nEmail: {user_data['email']}\nPhone: {user_data['phone']}\n\nThank you for registering!"
                    mail.send(msg)
                except Exception as e:
                    flash(f"Error sending confirmation email: {str(e)}", "danger")

                flash("Registration successful!", "success")
                return redirect(url_for('login'))
            
            flash("User data missing, please sign up again.", "danger")
            return redirect(url_for('signup'))
        else:
            flash("Invalid OTP, try again.", "danger")

    return render_template('verify_otp.html')

@app.route('/resend_otp', methods=['GET'])
def resend_otp():
    if 'otp_time' in session and time.time() - session['otp_time'] < 60:
        flash("Please wait before requesting a new OTP.", "warning")
        return redirect(url_for('verify_otp'))
    
    # Generate new OTP
    otp = random.randint(100000, 999999)
    session['otp'] = otp
    session['otp_time'] = time.time()

    # Resend OTP to email
    user_data = session.get('user_data', {})
    if 'email' in user_data:
        try:
            msg = Message("Your New OTP Code", recipients=[user_data['email']])
            msg.body = f"Your new OTP for registration is {otp}. It will expire in 5 minutes."
            mail.send(msg)
            flash("New OTP sent to your email!", "success")
        except smtplib.SMTPException as e:
            flash(f"Error sending email: {str(e)}", "danger")
    else:
        flash("Session expired. Please sign up again.", "danger")
        return redirect(url_for('signup'))
    
    return redirect(url_for('verify_otp'))



# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.context_processor
def inject_user_email():
    if current_user.is_authenticated:
        return dict(user_email=current_user.email)
    return dict(user_email=None)


# Protected Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.name)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email not found.', 'danger')
            return redirect(url_for('forgot_password'))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('forgot_password'))

        # Hash the new password and update
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        flash('Password reset successfully. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')




# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')

    # Redirect to login page with a refresh flag
    response = redirect(url_for('login', refresh='true'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

#

# Protected Service Routes
@app.route('/setgl')
@login_required
def setgl():
    return render_template('setgl.html', name=current_user.name)

@app.route('/goalset')
@login_required
def goalset():
    return render_template('goalset.html', name=current_user.name)

@app.route('/meal')
@login_required
def meal():
    return render_template('meal.html', name=current_user.name)

@app.route('/stats')
@login_required
def stats():
    return render_template('stats.html', name=current_user.name)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

from flask_login import current_user

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')  # current_user is auto available in Jinja2


@app.route('/users')
@login_required
def users():
    users = User.query.all()
    contacts = Contact.query.all()  # ✅ Fetch contacts from DB
    print(contacts)  # Debugging: Check if contacts are fetched
    return render_template('users.html', users=users, contacts=contacts)

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not bcrypt.check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return render_template('settings.html', active_tab='change-password')

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return render_template('settings.html', active_tab='change-password')

    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    current_user.password = hashed_password
    db.session.commit()
    flash('Password updated successfully!', 'success')
    return render_template('settings.html', active_tab='change-password')


# Reset Password Route
@app.route('/reset_password', methods=['POST'])
@login_required
def reset_password():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password')

        if not user_id or not new_password:
            return jsonify({'success': False, 'message': 'Missing user ID or new password'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Update password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        return jsonify({'success': True, 'message': 'Password has been updated successfully.'})

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print("Error resetting password:", str(e))  # Log the error in terminal
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
    
# delete user 
@app.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'User deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting user: {str(e)}'}), 500
    

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return render_template('admin_login.html')

@app.route('/delete_contact', methods=['POST'])
def delete_contact():
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')

        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({"success": False, "message": "Contact not found"}), 404

        db.session.delete(contact)
        db.session.commit()

        return jsonify({"success": True, "message": "Contact deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error deleting contact: {str(e)}"}), 500


@app.route('/admin/contact-us')
def contact_us():
    contacts = Contact.query.all()
    print("Contacts retrieved:", contacts)  # Debugging line
    return render_template('admin_contact.html', contacts=contacts)


@app.route('/send_email', methods=['POST'])
@login_required
def send_email():
    print("🔹 Received send_email request")  # Log request

    data = request.get_json()
    print("📩 Request Data:", data)  # Log request data

    contact_id = data.get('contact_id')
    contact = Contact.query.get(contact_id)

    if not contact:
        print("❌ Contact not found!")
        return jsonify({"success": False, "message": "Contact not found"}), 404

    try:
        msg = Message("Response to Your Query",
                      recipients=[contact.email])
        msg.body = f"Hello {contact.name},\n\nThank you for reaching out! We will get back to you soon.\n\nBest Regards,\nAdmin Team"

        mail.send(msg)
        print(f"✅ Email sent to {contact.email}")
        return jsonify({"success": True, "message": "Email sent successfully"})

    except Exception as e:
        print(f"❌ Email Error: {str(e)}")  # Log email error
        return jsonify({"success": False, "message": f"Error sending email: {str(e)}"}), 500


    
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print(app.url_map)
    app.run(debug=True, host='0.0.0.0', port=5000)