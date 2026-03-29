import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase_config import supabase

app = Flask(__name__)
CORS(app)

# --- FEATURE #2: ROLE-BASED ACCESS CONTROL ---
def get_user_profile(token):
    try:
        # Verify the user using the token from the frontend
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        
        # Fetch the profile from our custom 'profiles' table
        profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return profile.data
    except Exception as e:
        return None

# --- FEATURE #18: REGISTRATION & APPROVAL SYSTEM ---
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'student') # Default to student

    try:
        # 1. Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if auth_response.user:
            # 2. Create the profile in our 'profiles' table (Feature #4)
            user_id = auth_response.user.id
            supabase.table("profiles").insert({
                "id": user_id,
                "full_name": full_name,
                "role": role,
                "is_approved": False # Needs admin approval (Feature #18)
            }).execute()
            
            return jsonify({"message": "Registration successful. Waiting for Admin approval."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def status():
    return jsonify({"status": "Edu-Platform Backend is Online", "features": "Auth & Roles Loaded"})

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
