import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- DATABASE CONNECTION (SUPABASE) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- AI BRAIN SETUP (GEMINI PRO) ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- UNIVERSAL SECURITY ENGINE (FEATURE #2 & #17) ---
def verify_role(token, allowed_roles):
    """
    Checks the JWT token and verifies if the user has the 
    required permissions (Super Admin bypasses all checks).
    """
    try:
        if not token: return None
        # Clean the token if "Bearer " is included
        jwt = token.replace("Bearer ", "")
        user = supabase.auth.get_user(jwt)
        
        if user:
            # Fetch profile for role-based access
            profile = supabase.table("profiles").select("*").eq("id", user.user.id).single().execute()
            user_data = profile.data
            
            # GOD MODE: Super Admin can access EVERYTHING
            if user_data['role'] == 'super_admin':
                return user_data
            
            # Check if user role is in the allowed list for this route
            if user_data['role'] in allowed_roles:
                return user_data
        return None
    except Exception as e:
        print(f"Security Error: {str(e)}")
        return None

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "EDU-AI Cloud Core Online", "version": "2.0.1"}), 200

# --- PART 2 WILL HANDLE AUTH & REGISTRATION ---
# --- FEATURE #1: UNIVERSAL AUTH & REGISTRATION (REPLACING PREVIOUS AUTH) ---

@app.route('/register', methods=['POST'])
def register():
    """
    Handles both New Signups and Existing Logins.
    Logic: If user exists, try to log in. If not, create them.
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    try:
        # Try logging in first (to see if they exist)
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # If login successful, get their profile/role
        profile = supabase.table("profiles").select("*").eq("id", res.user.id).single().execute()
        user_data = profile.data

        # Check if user is approved (Feature #18)
        if not user_data.get('is_approved') and user_data['role'] != 'super_admin':
            return jsonify({"error": "Account pending Admin approval. Contact your Institute."}), 403

        return jsonify({
            "message": "Login successful",
            "token": res.session.access_token,
            "role": user_data['role'],
            "full_name": user_data['full_name']
        }), 200

    except Exception:
        # If login fails, try to Register them as a new user
        try:
            signup_res = supabase.auth.sign_up({"email": email, "password": password})
            
            # Default Role: Student (Feature #1)
            # Default Status: Not Approved (Feature #18)
            new_profile = {
                "id": signup_res.user.id,
                "email": email,
                "full_name": email.split('@')[0], # Temp name from email
                "role": "student",
                "is_approved": False,
                "xp": 0,
                "level": 1
            }
            
            supabase.table("profiles").insert(new_profile).execute()
            
            return jsonify({
                "message": "Registration successful. Awaiting Admin Approval.",
                "status": "pending"
            }), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# --- FEATURE #18: ADMIN APPROVAL SYSTEM ---

@app.route('/admin/approve-user', methods=['POST'])
def approve_user():
    """
    Only Super Admin or Institute Admin can approve new students.
    """
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin', 'inst_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    target_user_id = request.json.get('user_id')
    
    # Update user status to Approved
    supabase.table("profiles").update({"is_approved": True}).eq("id", target_user_id).execute()
    
    return jsonify({"message": "User approved successfully"}), 200

# --- PART 3 WILL HANDLE BATCHES, PAYMENTS & AI DOUBT SOLVING ---
# --- FEATURE #6 & #8: BATCH & PAYMENT SYSTEM ---

@app.route('/payment/submit', methods=['POST'])
def submit_payment():
    """
    Feature #7: Students upload their QR screenshot link and amount.
    Status remains 'pending' until Admin approves.
    """
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    payment_data = {
        "user_id": user['id'],
        "amount": data.get('amount'),
        "screenshot_url": data.get('screenshot_url'),
        "batch_id": data.get('batch_id'),
        "status": "pending",
        "coupon_used": data.get('coupon_code', None),
        "created_at": datetime.now().isoformat()
    }

    # Log payment request in Supabase
    supabase.table("payments").insert(payment_data).execute()
    
    return jsonify({"message": "Payment submitted. Awaiting Admin verification."}), 201

@app.route('/admin/approve-payment', methods=['POST'])
def approve_payment():
    """
    Feature #20: Auto-enrollment after payment approval.
    """
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin', 'inst_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    payment_id = request.json.get('payment_id')
    
    # 1. Get Payment Details
    pay_res = supabase.table("payments").select("*").eq("id", payment_id).single().execute()
    pay_data = pay_res.data

    # 2. Approve Payment
    supabase.table("payments").update({"status": "approved"}).eq("id", payment_id).execute()

    # 3. Auto-Enroll Student (Feature #20)
    supabase.table("enrollments").insert({
        "user_id": pay_data['user_id'],
        "batch_id": pay_data['batch_id']
    }).execute()

    # 4. Award XP (Feature #5 Gamification)
    supabase.rpc('increment_xp', {'user_id': pay_data['user_id'], 'xp_amount': 100}).execute()

    return jsonify({"message": "Payment Approved. Student enrolled and 100 XP awarded!"}), 200

# --- FEATURE #14: REAL GEMINI AI DOUBT SOLVER ---

@app.route('/ai/solve-doubt', methods=['POST'])
def solve_doubt():
    """
    Feature #14: Instant AI answers using your Gemini API Key.
    """
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student', 'teacher', 'super_admin'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"answer": "Please provide a question."}), 400

    try:
        # Construct professional academic prompt
        prompt = f"You are the Edu-AI Expert. Provide a detailed, step-by-step academic solution for: {question}"
        
        # Call Google Gemini API
        response = ai_model.generate_content(prompt)
        ai_answer = response.text

        # Feature #4: Log the interaction
        supabase.table("ai_logs").insert({
            "user_id": user['id'],
            "query": question,
            "response": ai_answer
        }).execute()

        return jsonify({"answer": ai_answer}), 200

    except Exception as e:
        print(f"AI Error: {str(e)}")
        return jsonify({"answer": "AI Brain is busy. Try again in a few seconds!"}), 500

# --- PART 4 WILL HANDLE EXAMS, PROCTORING LOGS & STATS ---
# --- FEATURE #10: AI PROCTORING & EXAM LOGGING ---

@app.route('/exams/log-proctor-event', methods=['POST'])
def log_proctor_event():
    """
    Feature #10: Logs suspicious activity (Tab switching, Face missing).
    Used by teachers to review student integrity.
    """
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    event = {
        "user_id": user['id'],
        "exam_id": data.get('exam_id'),
        "event_type": data.get('event_type'), # e.g., "TAB_SWITCH"
        "timestamp": datetime.now().isoformat()
    }

    # Store violation in Supabase
    supabase.table("proctor_logs").insert(event).execute()
    
    return jsonify({"message": "Proctoring event logged."}), 201

# --- FEATURE #19: GLOBAL ANALYTICS (FOR SUPER ADMIN) ---

@app.route('/admin/stats', methods=['GET'])
def get_global_stats():
    """
    Feature #19: Powers the "God Mode" Dashboard.
    Fetches totals for Revenue, Users, and Institutes.
    """
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    try:
        # 1. Get Total Users
        users_count = supabase.table("profiles").select("id", count="exact").execute()
        
        # 2. Get Total Revenue (Sum of approved payments)
        revenue_res = supabase.table("payments").select("amount").eq("status", "approved").execute()
        total_rev = sum(int(item['amount']) for item in revenue_res.data)

        # 3. Get Active Institutes
        inst_count = supabase.table("institutes").select("id", count="exact").execute()

        # 4. Get Pending Approvals
        pending_res = supabase.table("profiles").select("id", count="exact").eq("is_approved", False).execute()

        return jsonify({
            "total_users": users_count.count,
            "total_revenue": total_rev,
            "active_institutes": inst_count.count,
            "pending_approvals": pending_res.count
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- FEATURE #3: INSTITUTE CREATION (GOD MODE) ---

@app.route('/admin/create-institute', methods=['POST'])
def create_institute():
    """
    Feature #3: Super Admin creates a new Institute branch.
    """
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    new_inst = {
        "name": data.get('name'),
        "admin_email": data.get('email'),
        "features_enabled": data.get('features', ['ai_doubt', 'proctoring']),
        "created_at": datetime.now().isoformat()
    }

    supabase.table("institutes").insert(new_inst).execute()
    return jsonify({"message": f"Institute {data.get('name')} successfully deployed!"}), 201

# --- START THE CORE ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
