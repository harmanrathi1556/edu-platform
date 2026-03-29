from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import os
from config import Config
from models import Database
from utils.decorators import role_required
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Global DB instance
db = Database()

# Register blueprints (will be created later)
# from routes.auth_routes import auth_bp
# from routes.superadmin_routes import superadmin_bp
# app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

# Home route
@app.route('/')
def home():
    if 'user_id' in session:
        user = db.get_user_by_id(session['user_id'])
        if user and user['role'] == 'superadmin':
            return redirect(url_for('superadmin_dashboard'))
        elif user and user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user and user['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif user and user['role'] == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    flash('Access denied! Insufficient permissions.', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
