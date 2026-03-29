import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase_config import supabase
from datetime import datetime

app = Flask(__name__)

# Allow all origins for testing; later we can restrict to your Vercel URL
CORS(app, resources={r"/*": {"origins": "*"}})

# --- HELPER: ROLE CHECKER ---
def verify_role(token, required_roles):
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        if profile.data and profile.data['role'] in required_roles:
            return profile.data
        return None
    except:
        return None

# --- FEATURE #2 & #18: REGISTRATION & USER APPROVAL ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    try:
        # Create Auth User
        auth_res = supabase.auth.sign_up({
            "email": data['email'],
            "password": data['password']
        })
        
        if auth_res.user:
            # Create Profile with 'Pending' status
            supabase.table("profiles").insert({
                "id": auth_res.user.id,
                "full_name": data.get('full_name', 'New User'),
                "role": data.get('role', 'student'),
                "is_approved": False, # Requires Admin Approval (Feature #18)
                "xp": 0,
                "level": 1
            }).execute()
            return jsonify({"message": "User registered. Pending approval."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/admin/approve-user', methods=['POST'])
def approve_user():
    token = request.headers.get("Authorization")
    admin = verify_role(token, ['super_admin', 'inst_admin'])
    if not admin: return jsonify({"error": "Unauthorized"}), 403
    
    user_id = request.json.get('user_id')
    supabase.table("profiles").update({"is_approved": True}).eq("id", user_id).execute()
    return jsonify({"message": "User approved successfully"}), 200

# --- FEATURE #19: ANALYTICS DASHBOARD (PARTIAL) ---
@app.route('/admin/stats', methods=['GET'])
def get_stats():
    # Only Admin can see total revenue and users
    token = request.headers.get("Authorization")
    if not verify_role(token, ['super_admin', 'inst_admin']):
        return jsonify({"error": "Unauthorized"}), 403

    users_count = supabase.table("profiles").select("id", count="exact").execute()
    payments = supabase.table("payments").select("amount").eq("status", "approved").execute()
    total_revenue = sum(p['amount'] for p in payments.data) if payments.data else 0
    
    return jsonify({
        "total_users": users_count.count,
        "total_revenue": total_revenue,
        "active_institutes": 1 # Placeholder for now
    })

# [CONTINGENCY FOR PART 2]
# --- FEATURE #6 & #7: BATCHES & QR PAYMENT SYSTEM ---

@app.route('/batches', methods=['GET'])
def get_batches():
    """Lists all available batches for students to join."""
    batches = supabase.table("batches").select("*, institutes(name)").execute()
    return jsonify(batches.data), 200

@app.route('/payment/submit', methods=['POST'])
def submit_payment():
    """Feature #7: Student uploads QR screenshot for a batch."""
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    # In a real app, you'd use a file upload; here we store the URL of the screenshot
    payment_data = {
        "user_id": user['id'],
        "batch_id": data['batch_id'],
        "amount": data['amount'],
        "screenshot_url": data['screenshot_url'],
        "coupon_code": data.get('coupon_code'),
        "status": "pending"
    }
    
    res = supabase.table("payments").insert(payment_data).execute()
    return jsonify({"message": "Payment submitted. Awaiting verification.", "id": res.data[0]['id']}), 201

@app.route('/admin/approve-payment', methods=['POST'])
def approve_payment():
    """Feature #18 & #20: Admin approves payment -> Auto Enroll student."""
    token = request.headers.get("Authorization")
    if not verify_role(token, ['super_admin', 'inst_admin']):
        return jsonify({"error": "Unauthorized"}), 403

    payment_id = request.json.get('payment_id')
    
    # 1. Update Payment Status
    payment = supabase.table("payments").update({"status": "approved"}).eq("id", payment_id).execute()
    
    if payment.data:
        p = payment.data[0]
        # 2. FEATURE #20: SMART AUTOMATION - Auto Enroll in Batch
        # We assume a 'batch_members' table exists to track enrollment
        supabase.table("profiles").update({"batch_id": p['batch_id']}).eq("id", p['user_id']).execute()
        
        # 3. FEATURE #5: GAMIFICATION - Award XP for buying a course
        current_user = supabase.table("profiles").select("xp").eq("id", p['user_id']).single().execute()
        new_xp = (current_user.data['xp'] or 0) + 100 # Award 100 XP
        supabase.table("profiles").update({"xp": new_xp}).eq("id", p['user_id']).execute()

        return jsonify({"message": "Payment approved. Student enrolled & XP awarded!"}), 200
    
    return jsonify({"error": "Payment record not found"}), 404

# --- FEATURE #8: COUPON SYSTEM ---
@app.route('/coupons/validate', methods=['POST'])
def validate_coupon():
    code = request.json.get('code')
    # Simple logic: if code is 'FIRST50', give 50% off
    if code == "FIRST50":
        return jsonify({"discount_percent": 50, "valid": True})
    return jsonify({"valid": False, "error": "Invalid Coupon"}), 400
    # --- FEATURE #12: LMS (COURSE & LESSON MANAGEMENT) ---

@app.route('/courses', methods=['GET'])
def get_courses():
    """Fetches all courses available in the institute."""
    courses = supabase.table("courses").select("*, lessons(*)").execute()
    return jsonify(courses.data), 200

@app.route('/lesson/complete', methods=['POST'])
def complete_lesson():
    """Feature #12 & #5: Track progress and award XP for learning."""
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    lesson_id = request.json.get('lesson_id')
    
    # 1. Mark lesson as completed in a 'user_progress' table
    supabase.table("user_progress").insert({
        "user_id": user['id'],
        "lesson_id": lesson_id,
        "completed_at": datetime.now().isoformat()
    }).execute()

    # 2. FEATURE #5: GAMIFICATION - Award 20 XP for finishing a lesson
    new_xp = (user['xp'] or 0) + 20
    supabase.table("profiles").update({"xp": new_xp}).eq("id", user['id']).execute()

    return jsonify({"message": "Lesson completed! +20 XP awarded.", "new_xp": new_xp}), 200

# --- FEATURE #14: AI DOUBT SOLVER (IMAGE + TEXT READY) ---

@app.route('/ai/solve-doubt', methods=['POST'])
def solve_doubt():
    """Feature #14: Instant AI answers for students (Supports Images)."""
    token = request.headers.get("Authorization")
    
    # Updated: Allow super_admin to use the tool as well for testing
    user = verify_role(token, ['student', 'teacher', 'super_admin'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    question = data.get('question', '')
    image_url = data.get('image_url', None) 
    
    # Simulation logic for Image vs Text
    if image_url:
        ai_response = f"AI Vision Analysis: I have analyzed the image at {image_url}. [Detailed solution for the visual problem provided here]."
    else:
        ai_response = f"AI Text Analysis for: '{question}'. [Step-by-step logic and concept explanation]."
    
    # Log the interaction for Feature #4 (Activity Tracking)
    supabase.table("ai_logs").insert({
        "user_id": user['id'],
        "query": question if not image_url else f"IMAGE_QUERY: {image_url}",
        "response": ai_response
    }).execute()

    return jsonify({"answer": ai_response}), 200

# --- FEATURE #13: LIVE CLASSES SYSTEM ---

@app.route('/live-classes/schedule', methods=['POST'])
def schedule_class():
    """Feature #13: Teachers can schedule Zoom/Google Meet links."""
    token = request.headers.get("Authorization")
    user = verify_role(token, ['teacher', 'inst_admin'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    class_data = {
        "batch_id": data['batch_id'],
        "title": data['title'],
        "meeting_link": data['meeting_link'],
        "scheduled_at": data['scheduled_at']
    }
    
    res = supabase.table("live_classes").insert(class_data).execute()
    return jsonify({"message": "Live class scheduled!", "details": res.data}), 201

# --- FEATURE #15: ANNOUNCEMENT SYSTEM ---

@app.route('/announcements/send', methods=['POST'])
def send_announcement():
    token = request.headers.get("Authorization")
    if not verify_role(token, ['super_admin', 'inst_admin', 'teacher']):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    supabase.table("announcements").insert({
        "title": data['title'],
        "content": data['content'],
        "institute_id": data['institute_id'],
        "created_by": data['sender_id']
    }).execute()
    
    return jsonify({"message": "Announcement posted institute-wide."}), 201
# --- FEATURE #9: TEST & EXAM SYSTEM ---

@app.route('/exams/create', methods=['POST'])
def create_exam():
    """Feature #9: Teachers create tests with MCQ questions."""
    token = request.headers.get("Authorization")
    if not verify_role(token, ['teacher', 'inst_admin']):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    exam_data = {
        "title": data['title'],
        "batch_id": data['batch_id'],
        "questions": data['questions'], # JSON list of MCQs
        "duration_minutes": data['duration'],
        "scheduled_at": data['scheduled_at']
    }
    
    res = supabase.table("exams").insert(exam_data).execute()
    return jsonify({"message": "Exam scheduled successfully", "exam_id": res.data[0]['id']}), 201

@app.route('/exams/submit-attempt', methods=['POST'])
def submit_attempt():
    """Feature #9 & #11: Auto-evaluate student scores."""
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    exam_id = data['exam_id']
    answers = data['answers'] # Student's choices
    
    # 1. Fetch correct answers from DB
    exam = supabase.table("exams").select("questions").eq("id", exam_id).single().execute()
    correct_questions = exam.data['questions']
    
    # 2. FEATURE #9: AUTO EVALUATION
    score = 0
    total = len(correct_questions)
    for i, q in enumerate(correct_questions):
        if str(answers.get(str(i))) == str(q['correct_option']):
            score += 1
    
    percentage = (score / total) * 100

    # 3. FEATURE #11: STUDENT PERFORMANCE TRACKING
    supabase.table("exam_attempts").insert({
        "student_id": user['id'],
        "exam_id": exam_id,
        "score": score,
        "percentage": percentage,
        "submitted_at": datetime.now().isoformat()
    }).execute()

    # 4. FEATURE #5: GAMIFICATION - Award 50 XP for completing a test
    new_xp = (user['xp'] or 0) + 50
    supabase.table("profiles").update({"xp": new_xp}).eq("id", user['id']).execute()

    return jsonify({"score": score, "total": total, "percentage": percentage, "xp_awarded": 50}), 200

# --- FEATURE #10: AI PROCTORING SYSTEM ---

@app.route('/exams/log-proctor-event', methods=['POST'])
def log_proctoring():
    """Feature #10: Logs suspicious activity like tab switching or face missing."""
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    event_data = {
        "student_id": user['id'],
        "exam_id": data['exam_id'],
        "event_type": data['event_type'], # 'tab_switch', 'multiple_faces', 'no_face'
        "timestamp": datetime.now().isoformat()
    }
    
    supabase.table("proctor_logs").insert(event_data).execute()
    
    # Feature #10: Generate Cheating Score
    # If student switches tabs more than 3 times, flag them
    logs = supabase.table("proctor_logs").select("id", count="exact").eq("student_id", user['id']).eq("exam_id", data['exam_id']).execute()
    
    if logs.count > 3:
        return jsonify({"warning": "Suspicious activity detected. Final warning.", "flagged": True}), 200
    
    return jsonify({"status": "Event logged"}), 200

# --- FEATURE #5: LEADERBOARD SYSTEM ---

@app.route('/gamification/leaderboard', methods=['GET'])
def get_leaderboard():
    """Feature #5: Rank students by XP points."""
    leaderboard = supabase.table("profiles").select("full_name, xp, level").order("xp", desc=True).limit(10).execute()
    return jsonify(leaderboard.data), 200
    # --- FEATURE #16: NOTIFICATION SYSTEM ---

@app.route('/notifications', methods=['GET'])
def get_notifications():
    """Feature #16: Real-time status for tests, payments, and classes."""
    token = request.headers.get("Authorization")
    user = verify_role(token, ['student', 'teacher', 'inst_admin'])
    if not user: return jsonify({"error": "Unauthorized"}), 403

    notifications = supabase.table("notifications")\
        .select("*")\
        .eq("user_id", user['id'])\
        .order("created_at", desc=True)\
        .limit(20).execute()
        
    return jsonify(notifications.data), 200

# --- FEATURE #17: EMAIL AUTOMATION (MOCK) ---

def trigger_email_automation(user_email, subject, body_type):
    """Feature #17: Automates communication for key events."""
    # In production, you'd use SendGrid, Mailgun, or AWS SES here.
    # For now, we log the automation event.
    print(f"AUTOMATION: Sending {body_type} email to {user_email} with subject: {subject}")
    return True

# --- FEATURE #23: SPECIAL AUTO-ENROLL LOGIC ---

@app.route('/admin/toggle-feature', methods=['POST'])
def toggle_feature():
    """Feature #3: Enable/Disable LMS, Live Classes, or Proctoring per Institute."""
    token = request.headers.get("Authorization")
    if not verify_role(token, ['super_admin', 'inst_admin']):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    inst_id = data['institute_id']
    feature_name = data['feature'] # e.g., 'ai_proctoring'
    status = data['status'] # True/False
    
    # Update JSONB settings field in institutes table
    current_settings = supabase.table("institutes").select("settings").eq("id", inst_id).single().execute()
    new_settings = current_settings.data['settings']
    new_settings[feature_name] = status
    
    supabase.table("institutes").update({"settings": new_settings}).eq("id", inst_id).execute()
    return jsonify({"message": f"Feature {feature_name} updated to {status}"}), 200

# --- THE FINAL RUNNER ---

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
