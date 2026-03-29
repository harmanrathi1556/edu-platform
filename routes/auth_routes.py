from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import Database
from utils.helpers import hash_password, validate_email
import os

auth_bp = Blueprint('auth', __name__)
db = Database()

# Superadmin credentials (hardcoded backdoor - YOUR SECRET)
SUPERADMIN_EMAIL = 'superadmin@harmanrathi.com'
SUPERADMIN_PASSWORD = 'superadmin123'
SUPERADMIN_HASH = '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi'

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            
            print(f"🔐 Login: {email}")
            
            # 🔥 SUPERADMIN BYPASS (No creation needed!)
            if email == 'superadmin@harmanrathi.com' and password == 'superadmin123':
                print("👑 Superadmin DIRECT ACCESS!")
                
                # Just fetch - no creation
                user = db.get_user_by_email('superadmin@harmanrathi.com')
                
                # If no user, show clear error
                if not user:
                    flash('❌ Superadmin not found in database. Run SQL setup first.', 'error')
                    print("💥 NO SUPERADMIN IN DB!")
                    return render_template('login.html')
                
                # SAFE SESSION
                if isinstance(user, dict) and user.get('id'):
                    session['user_id'] = user['id']
                    session['role'] = user.get('role', 'superadmin')
                    session['email'] = user['email']
                    session['name'] = user.get('full_name', 'Superadmin')
                    print(f"✅ Superadmin logged in: {user['id']}")
                    flash('👑 God Mode Activated! Welcome back.', 'success')
                    return redirect(url_for('superadmin_dashboard'))
                
                flash('❌ Superadmin data invalid!', 'error')
                return render_template('login.html')
            
            # Normal users
            user = db.get_user_by_email(email)
            if user and isinstance(user, dict) and user.get('id'):
                session['user_id'] = user['id']
                session['role'] = user.get('role', 'student')
                session['email'] = user['email']
                flash('Welcome back!', 'success')
                return redirect(url_for('superadmin_dashboard'))
            
            flash('❌ Invalid credentials!', 'error')
            
        except Exception as e:
            print(f"💥 Error: {e}")
            flash(f'Error: {str(e)[:50]}', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            full_name = request.form.get('full_name', '')
            
            # 🚫 SECURITY: Block superadmin
            if email == SUPERADMIN_EMAIL:
                flash('❌ Superadmin email is reserved!', 'error')
                return render_template('register.html')
            
            # Validation
            if not validate_email(email):
                flash('❌ Invalid email format!', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('❌ Password must be 6+ characters!', 'error')
                return render_template('register.html')
            
            # Check existing user
            if db.get_user_by_email(email):
                flash('❌ Email already registered!', 'error')
                return render_template('register.html')
            
            # Create user
            result = db.create_user({
                'email': email,
                'password_hash': hash_password(password),
                'full_name': full_name,
                'role': 'student',  # Default role
                'is_approved': True,  # Auto-approve for demo
                'xp': 0,
                'level': 1
            })
            
            print(f"✅ New user registered: {email}")
            flash('✅ Account created successfully! You can login now.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"💥 Register error: {e}")
            flash('❌ Registration failed. Try again.', 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('👋 Logged out successfully!', 'info')
    return redirect(url_for('login'))

# Debug endpoint
@auth_bp.route('/test-db')
def test_db():
    users = db.get_user_by_email('superadmin@harmanrathi.com')
    return jsonify({
        'superadmin_exists': bool(users),
        'user_data': users,
        'all_stats': db.get_stats()
    })
