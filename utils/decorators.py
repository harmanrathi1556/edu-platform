from functools import wraps
from flask import session, redirect, url_for, flash, request
from models import Database

db = Database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first!', 'warning')
                return redirect(url_for('login'))
            
            user = db.get_user_by_id(session['user_id'])
            if not user or user['role'] not in roles:
                flash('Access denied! You need specific permissions.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def institute_admin_only(institute_id=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user = db.get_user_by_id(session['user_id'])
            if user['role'] not in ['superadmin', 'admin']:
                flash('Admin access required!', 'error')
                return redirect(url_for('home'))
            
            # Check institute ownership for admins
            if user['role'] == 'admin' and institute_id:
                institute = db.supabase.table('institutes').select('admin_id').eq('id', institute_id).execute()
                if not institute.data or institute.data[0]['admin_id'] != session['user_id']:
                    flash('You can only manage your own institute!', 'error')
                    return redirect(url_for('admin_dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
