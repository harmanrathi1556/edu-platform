from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import os
from config import Config
from models import Database
from utils.decorators import login_required
from dotenv import load_dotenv
from routes.auth_routes import auth_bp

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Global DB instance
db = Database()

# 🔥 DEBUG ROUTE (REMOVE LATER)
@app.route('/debug')
def debug():
    try:
        stats = db.get_stats()
        return jsonify({
            'status': 'OK',
            'supabase_url': str(Config.SUPABASE_URL)[:30] + '...',
            'env_vars': {
                'has_supabase': bool(Config.SUPABASE_URL),
                'has_key': bool(Config.SUPABASE_KEY)
            },
            'stats': stats,
            'session': dict(session)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'trace': str(type(e))}), 500

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Home route
@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'superadmin':
            return redirect(url_for('superadmin_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif role == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('auth.login'))

# Dashboards (Safe versions)
@app.route('/superadmin')
def superadmin_dashboard():
    try:
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        stats = db.get_stats()
        institutes = db.get_institutes()
        return render_template('superadmin.html', stats=stats, institutes=institutes)
    except:
        flash('Dashboard loading error', 'error')
        return redirect(url_for('auth.login'))

@app.route('/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/teacher')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/student')
def student_dashboard():
    return render_template('student_dashboard.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    flash('Server error occurred. Please try again.', 'error')
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
