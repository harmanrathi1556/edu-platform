import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- SECURE CLOUD CONNECTIONS ---
# Fetches your renamed variables from Render Environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") 

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ WARNING: Database keys missing. Check Render Env Variables.")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- AI BRAIN: GEMINI 1.5 FLASH ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- THE GUARDIAN: UNIVERSAL SECURITY & GOD MODE ---
def verify_role(token, allowed_roles):
    """
    Validates the user. If the user is Harman Rathi (super_admin), 
    the gate opens for everything automatically.
    """
    try:
        if not token: return None
        jwt = token.replace("Bearer ", "")
        user = supabase.auth.get_user(jwt)
        
        if user:
            # Fetch profile to check the role
            profile = supabase.table("profiles").select("*").eq("id", user.user.id).single().execute()
            user_data = profile.data
            
            # HARMAN RATHI GOD MODE CHECK
            if user_data['role'] == 'super_admin':
                return user_data # Full access granted
            
            # Standard Role Check for others
            if user_data['role'] in allowed_roles:
                return user_data
        return None
    except Exception as e:
        print(f"Security Shield Blocked Access: {str(e)}")
        return None

@app.route('/', methods=['GET'])
def system_status():
    return jsonify({
        "status": "Live",
        "engine": "EDU-AI Quantum Core",
        "admin": "Harman Rathi"
    }), 200
    # --- FEATURE #1, #2, & #18: UNIFIED AUTH & APPROVAL ENGINE ---

@app.route('/register', methods=['POST'])
def register():
    """
    Handles Multi-role Login & Secure Authentication.
    If new: Creates account as 'Pending'.
    If existing: Grants access based on Role & Approval status.
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        # 1. Sign in with Supabase Auth
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # 2. Fetch Detailed Profile (Feature #21)
        profile = supabase.table("profiles").select("*").eq("id", res.user.id).single().execute()
        u = profile.data

        # 3. Security Check: Approval & Role (Feature #18)
        # Super Admin (Harman) is always approved.
        if u['role'] != 'super_admin' and not u.get('is_approved'):
            return jsonify({"error": "Access Denied: Account pending approval by Harman Rathi."}), 403

        return jsonify({
            "token": res.session.access_token,
            "role": u['role'],
            "name": u['full_name'],
            "inst_id": u.get('institute_id')
        }), 200

    except Exception:
        # 4. Handle New Registration (Feature #3 & #4)
        try:
            signup = supabase.auth.sign_up({"email": email, "password": password})
            
            new_user = {
                "id": signup.user.id,
                "email": email,
                "full_name": email.split('@')[0],
                "role": "student", # Default signup role
                "is_approved": False,
                "xp": 0, "level": 1,
                "created_at": datetime.now().isoformat()
            }
            
            supabase.table("profiles").insert(new_user).execute()
            return jsonify({"message": "Account created. Awaiting manual approval."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# --- FEATURE #3, #15, & #21: ADMIN COMMAND CENTER ---

@app.route('/admin/approve-user', methods=['POST'])
def approve_user():
    """
    Feature #18: Manual Approval/Rejection System.
    """
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin', 'inst_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    target_id = request.json.get('user_id')
    status = request.json.get('approve', True) # True to approve, False to reject

    if status:
        supabase.table("profiles").update({"is_approved": True}).eq("id", target_id).execute()
        return jsonify({"message": "User Approved Successfully"}), 200
    else:
        # Feature #4: Delete/Reject User
        supabase.table("profiles").delete().eq("id", target_id).execute()
        return jsonify({"message": "User Rejected and Removed"}), 200

@app.route('/admin/bulk-upload', methods=['POST'])
def bulk_upload():
    """
    Feature #22: Bulk Student Upload via List.
    """
    token = request.headers.get("Authorization")
    if not verify_role(token, ['super_admin', 'inst_admin']): 
        return jsonify({"error": "Unauthorized"}), 403

    students = request.json.get('students', []) # List of user objects
    for s in students:
        # Logic to create multiple users in Supabase Auth & Profiles
        pass
    return jsonify({"message": f"Processing {len(students)} students..."}), 200

# --- FEATURE #6: BATCH & TEACHER ASSIGNMENT ---

@app.route('/admin/create-batch', methods=['POST'])
def create_batch():
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin', 'inst_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    batch_data = {
        "name": data.get('name'),
        "institute_id": admin.get('institute_id'),
        "teacher_id": data.get('teacher_id'),
        "created_at": datetime.now().isoformat()
    }
    
    supabase.table("batches").insert(batch_data).execute()
    return jsonify({"message": "New Batch Initialized"}), 201
    # --- FEATURE #7 & #8: SECURE QR PAYMENT & AUTO-ENROLLMENT ---

@app.route('/payment/submit', methods=['POST'])
def submit_payment():
    """
    Feature #7: Students upload their QR screenshot link.
    Stored for Admin verification (Feature #18).
    """
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    p_entry = {
        "user_id": user['id'],
        "amount": data.get('amount'),
        "screenshot_url": data.get('screenshot_url'),
        "batch_id": data.get('batch_id'),
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    supabase.table("payments").insert(p_entry).execute()
    return jsonify({"message": "Proof uploaded! Waiting for Admin Approval."}), 201

@app.route('/admin/approve-payment', methods=['POST'])
def approve_payment():
    """
    Feature #20: The "Magic" Automation.
    Once approved, the student is auto-enrolled and awarded XP.
    """
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin', 'inst_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    payment_id = request.json.get('payment_id')
    pay_data = supabase.table("payments").select("*").eq("id", payment_id).single().execute().data

    # 1. Update Status
    supabase.table("payments").update({"status": "approved"}).eq("id", payment_id).execute()

    # 2. AUTO-ENROLL (Feature #20)
    supabase.table("enrollments").insert({
        "user_id": pay_data['user_id'],
        "batch_id": pay_data['batch_id']
    }).execute()

    # 3. GAMIFICATION (Feature #5): Award 200 XP for enrollment
    supabase.rpc('increment_xp', {'u_id': pay_data['user_id'], 'xp_amt': 200}).execute()

    return jsonify({"message": "Student Enrolled & XP Awarded!"}), 200

# --- FEATURE #14: REAL-TIME AI DOUBT SOLVER (GEMINI 1.5) ---

@app.route('/ai/solve-doubt', methods=['POST'])
def solve_doubt():
    """
    Feature #14: Instant AI solutions for Math/Science.
    """
    token = request.headers.get("Authorization")
    if not verify_role(token, ['student', 'teacher', 'super_admin']): 
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    question = data.get('question')

    try:
        # System Prompt ensures AI stays as a professional teacher
        prompt = f"Edu-AI Teacher Mode: Solve this academic doubt clearly: {question}"
        response = ai_model.generate_content(prompt)
        
        # Log usage for analytics (Feature #19)
        supabase.table("ai_logs").insert({"user_id": "system", "query": question}).execute()

        return jsonify({"answer": response.text}), 200
    except Exception as e:
        return jsonify({"answer": "AI Brain is currently syncing. Retry in 10s."}), 500

# --- FEATURE #10: AI PROCTORING LOGS (INTEGRITY GUARD) ---

@app.route('/exams/log-violation', methods=['POST'])
def log_violation():
    """
    Feature #10: Detects Tab Switches or Face Missing.
    Used for Feature #21 (Violation Reports).
    """
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    violation = {
        "user_id": user['id'],
        "exam_id": data.get('exam_id'),
        "type": data.get('type'), # e.g., 'TAB_SWITCH'
        "timestamp": datetime.now().isoformat()
    }
    
    supabase.table("proctor_logs").insert(violation).execute()
    return jsonify({"status": "Logged"}), 201

# --- START UP ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Gunicorn handles this on Render
    app.run(host='0.0.0.0', port=port)
