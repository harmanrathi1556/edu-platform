from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.helpers import hash_password, verify_password, validate_email
from models import Database

auth_bp = Blueprint('auth', __name__)

db = Database()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = db.get_user_by_email(email)
        if user and verify_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['email'] = user['email']
            
            # Update last login
            db.update_user(user['id'], {'last_login': 'NOW()'})
            
            flash('Login successful! Welcome back.', 'success')
            
            if user['role'] == 'superadmin':
                return redirect(url_for('superadmin_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form.get('role', 'student')
        institute_id = request.form.get('institute_id')
        
        if not validate_email(email):
            flash('Invalid email format!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('register.html')
        
        existing_user = db.get_user_by_email(email)
        if existing_user:
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        user_data = {
            'email': email,
            'password_hash': hash_password(password),
            'full_name': full_name,
            'role': role,
            'institute_id': institute_id,
            'is_approved': role == 'superadmin'  # Auto-approve superadmin
        }
        
        db.create_user(user_data)
        flash('Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))
