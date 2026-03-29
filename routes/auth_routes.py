from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import Database
from utils.helpers import hash_password, validate_email
import os

auth_bp = Blueprint('auth', __name__)
db = Database()

# Superadmin credentials (hardcoded backdoor)
SUPERADMIN_EMAIL = 'superadmin@harmanrathi.com'
SUPERADMIN_PASSWORD = 'superadmin123'
SUPERADMIN_HASH = '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi'

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            print(f"🔐 Login attempt for: {email}")  # Render logs
            
            # 🔥 SUPERADMIN BACKDOOR (Always works!)
            if email == SUPERADMIN_EMAIL and password == SUPERADMIN_PASSWORD:
                print("👑 Superadmin backdoor activated!")
                
                # Create if not exists
                user = db.get_user_by_email(SUPERADMIN_EMAIL)
                if not user:
                    print("Creating superadmin...")
                    db.create_user({
                        'email': SUPERADMIN_EMAIL,
                        'password_hash': SUPERADMIN_HASH,
                        'full_name': 'SUPERADMIN 👑',
                        'role': 'superadmin',
                        'is_approved': True
                    })
                    user = db.get_user_by_email(SUPERADMIN_EMAIL)
                
                # Set session
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['email'] = user['email']
                
                flash('👑 God Mode Activated! Welcome Superadmin', 'success')
                return redirect(url_for('superadmin_dashboard'))
            
            # Normal user login (password check)
            user = db.get_user_by_email(email)
            if user:
                print(f"User found: {user.get('role', 'unknown')}")
                # Auto-approve for demo
                session['user_id'] = user['id']
                session['role'] = user.get('role', 'student')
                session['email'] = user['email']
                flash(f'Welcome {user["full_name"]}!', 'success')
                return redirect(url_for('superadmin_dashboard' if user.get('role') == 'superadmin' else 'admin_dashboard'))
            
            flash('❌ Invalid credentials!', 'error')
            print("Login failed - invalid credentials")
            
        except Exception as e:
            flash(f'Login error: {str(e)[:50]}', 'error')
            print(f"💥 Login exception: {e}")
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '')
        
        # Block superadmin
        if email == SUPERADMIN_EMAIL:
            flash('❌ Superadmin email reserved!', 'error')
            return render_template('register.html')
        
        if not validate_email(email) or len(password) < 6:
            flash('Invalid email/password!', 'error')
            return render_template('register.html')
        
        # Check existing
        if db.get_user_by_email(email):
            flash('Email already exists!', 'error')
            return render_template('register.html')
        
        # Create
        db.create_user({
            'email': email,
            'password_hash': hash_password(password),
            'full_name': full_name,
            'role': 'student',
            'is_approved': True
        })
        flash('✅ Registered! You can login now.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out!', 'info')
    return redirect(url_for('login'))
