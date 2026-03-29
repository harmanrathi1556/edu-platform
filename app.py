from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import os
from config import Config
from models import Database
from utils.decorators import role_required, login_required
from dotenv import load_dotenv

# 🔥 IMPORT ALL ROUTES (Add more as we create them)
from routes.auth_routes import auth_bp

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Global DB instance
db = Database()

# 🔥 REGISTER ALL BLUEPRINTS
app.register_blueprint(auth_bp, url_prefix='/auth')

# Home route - Smart redirect based on role
@app.route('/')
def home():
    if 'user_id' in session:
        user = db.get_user_by_id(session['user_id'])
        if user:
            role = user['role']
            if role == 'superadmin':
                return redirect(url_for('superadmin_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif role == 'student':
                return redirect(url_for('student_dashboard'))
    return redirect(url_for('auth.login'))

# 🔥 SUPERADMIN DASHBOARD (TEMP UNTIL NEXT PART)
@app.route('/superadmin')
@login_required
def superadmin_dashboard():
    stats = db.get_stats()
    institutes = db.get_institutes().data or []
    return render_template('superadmin.html', stats=stats, institutes=institutes)

# 🔥 TEMP DASHBOARDS (Will expand later)
@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html', title="Admin Dashboard")

@app.route('/teacher')
@login_required
def teacher_dashboard():
    return render_template('teacher_dashboard.html', title="Teacher Dashboard")

@app.route('/student')
@login_required
def student_dashboard():
    return render_template('student_dashboard.html', title="Student Dashboard")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    flash('Access denied! Insufficient permissions.', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
