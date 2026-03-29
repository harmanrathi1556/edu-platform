import hashlib
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import Database

db = Database()

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, hash_):
    return check_password_hash(hash_, password)

def generate_file_name(original_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_name)
    return f"{name}_{timestamp}{ext}"

def get_user_stats():
    stats = db.get_stats()
    return {
        'total_users': stats.get('total_users', 0),
        'total_institutes': stats.get('total_institutes', 0),
        'total_payments': stats.get('total_payments', 0)
    }

def log_activity(user_id, action, details=""):
    # Future: Save to logs table
    print(f"LOG: User {user_id} - {action} - {details}")

def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
