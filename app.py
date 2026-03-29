from flask import Flask, render_template, request, redirect, session, jsonify
from supabase import create_client
from services.ai_service import solve_doubt
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =========================
# 🔗 SUPABASE CONNECTION
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 🧱 AUTO DATABASE SETUP (RESET TABLES)
# =========================
def setup_database():
    try:
        # Delete old data (SAFE RESET)
        supabase.table("users").delete().neq("id", "0").execute()
        supabase.table("institutes").delete().neq("id", "0").execute()
        supabase.table("payments").delete().neq("id", "0").execute()
    except:
        pass

    try:
        # Create default institute
        supabase.table("institutes").insert({
            "name": "Default Institute",
            "status": "active"
        }).execute()
    except:
        pass

# Run once
setup_database()

# =========================
# 🏠 HOME
# =========================
@app.route("/")
def home():
    return redirect("/login")

# =========================
# 📝 REGISTER PAGE
# =========================
@app.route("/register")
def register_page():
    institutes = supabase.table("institutes").select("*").execute().data
    return render_template("register.html", institutes=institutes)

# =========================
# 📝 REGISTER LOGIC
# =========================
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")
    institute_id = request.form.get("institute_id")

    supabase.table("users").insert({
        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "institute_id": institute_id
    }).execute()

    return redirect("/login")

# =========================
# 🔐 LOGIN PAGE
# =========================
@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    try:
        print("AI ROUTE HIT")

        # Try JSON first
        data = request.get_json(silent=True)

        if data:
            question = data.get("question")
        else:
            question = request.form.get("question")

        print("QUESTION:", question)

        if not question:
            return jsonify({"answer": "Please enter a question"})

        answer = solve_doubt(question)

        print("ANSWER:", answer)

        return jsonify({"answer": answer})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"answer": f"Server Error: {str(e)}"})

# =========================
# 🔐 LOGIN LOGIC
# =========================
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    user = supabase.table("users") \
        .select("*") \
        .eq("email", email) \
        .eq("password", password) \
        .execute().data

    if not user:
        return "Invalid credentials"

    user = user[0]

    if user["role"] != role:
        return "Role mismatch"

    session["user_id"] = user["id"]
    session["role"] = user["role"]

    if role == "superadmin":
        return redirect("/superadmin")
    elif role == "admin":
        return redirect("/admin")
    elif role == "teacher":
        return redirect("/teacher")
    else:
        return redirect("/student")

# =========================
# 🚪 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# ⚡ SUPER ADMIN DASHBOARD
# =========================
@app.route("/superadmin")
def superadmin():
    if "user_id" not in session or session.get("role") != "superadmin":
        return redirect("/login")

    users = supabase.table("users").select("*").execute().data
    institutes = supabase.table("institutes").select("*").execute().data
    payments = supabase.table("payments").select("*").execute().data

    return render_template(
        "dashboards/superadmin.html",
        users=users,
        institutes=institutes,
        payments=payments
    )

# =========================
# 🏫 CREATE INSTITUTE
# =========================
@app.route("/create_institute", methods=["POST"])
def create_institute():
    if session.get("role") != "superadmin":
        return redirect("/login")

    name = request.form.get("name")

    supabase.table("institutes").insert({
        "name": name,
        "status": "active"
    }).execute()

    return redirect("/superadmin")

# =========================
# 👤 CREATE ADMIN
# =========================
@app.route("/create_admin", methods=["POST"])
def create_admin():
    if session.get("role") != "superadmin":
        return redirect("/login")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    institute_id = request.form.get("institute_id")

    supabase.table("users").insert({
        "name": name,
        "email": email,
        "password": password,
        "role": "admin",
        "institute_id": institute_id
    }).execute()

    return redirect("/superadmin")
    # =========================
# 🏫 ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    user_id = session["user_id"]

    # Get current admin
    user = supabase.table("users").select("*").eq("id", user_id).execute().data[0]
    institute_id = user["institute_id"]

    # Fetch data of same institute
    students = supabase.table("users") \
        .select("*") \
        .eq("role", "student") \
        .eq("institute_id", institute_id) \
        .execute().data

    teachers = supabase.table("users") \
        .select("*") \
        .eq("role", "teacher") \
        .eq("institute_id", institute_id) \
        .execute().data

    payments = supabase.table("payments") \
        .select("*") \
        .eq("institute_id", institute_id) \
        .execute().data

    return render_template(
        "dashboards/admin.html",
        students=students,
        teachers=teachers,
        payments=payments
    )

# =========================
# 👨‍🏫 CREATE TEACHER
# =========================
@app.route("/create_teacher", methods=["POST"])
def create_teacher():
    if session.get("role") != "admin":
        return redirect("/login")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    user_id = session["user_id"]
    admin = supabase.table("users").select("*").eq("id", user_id).execute().data[0]

    supabase.table("users").insert({
        "name": name,
        "email": email,
        "password": password,
        "role": "teacher",
        "institute_id": admin["institute_id"]
    }).execute()

    return redirect("/admin")

# =========================
# 🎓 CREATE STUDENT
# =========================
@app.route("/create_student", methods=["POST"])
def create_student():
    if session.get("role") != "admin":
        return redirect("/login")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    user_id = session["user_id"]
    admin = supabase.table("users").select("*").eq("id", user_id).execute().data[0]

    supabase.table("users").insert({
        "name": name,
        "email": email,
        "password": password,
        "role": "student",
        "institute_id": admin["institute_id"]
    }).execute()

    return redirect("/admin")

# =========================
# 💳 UPLOAD PAYMENT (STUDENT)
# =========================
@app.route("/upload_payment", methods=["POST"])
def upload_payment():
    if session.get("role") != "student":
        return redirect("/login")

    screenshot = request.form.get("screenshot")  # for now text/url

    user_id = session["user_id"]
    student = supabase.table("users").select("*").eq("id", user_id).execute().data[0]

    supabase.table("payments").insert({
        "student_id": user_id,
        "institute_id": student["institute_id"],
        "screenshot": screenshot,
        "status": "pending"
    }).execute()

    return redirect("/student")

# =========================
# ✅ APPROVE PAYMENT
# =========================
@app.route("/approve_payment/<payment_id>")
def approve_payment(payment_id):
    if session.get("role") != "admin":
        return redirect("/login")

    supabase.table("payments").update({
        "status": "approved"
    }).eq("id", payment_id).execute()

    return redirect("/admin")

# =========================
# ❌ REJECT PAYMENT
# =========================
@app.route("/reject_payment/<payment_id>")
def reject_payment(payment_id):
    if session.get("role") != "admin":
        return redirect("/login")

    supabase.table("payments").update({
        "status": "rejected"
    }).eq("id", payment_id).execute()

    return redirect("/admin")

# =========================
# 👨‍🏫 TEACHER DASHBOARD
# =========================
@app.route("/teacher")
def teacher():
    if session.get("role") != "teacher":
        return redirect("/login")

    return render_template("dashboards/teacher.html")

# =========================
# 🎓 STUDENT DASHBOARD
# =========================
@app.route("/student")
def student():
    if session.get("role") != "student":
        return redirect("/login")

    user_id = session["user_id"]

    payments = supabase.table("payments") \
        .select("*") \
        .eq("student_id", user_id) \
        .execute().data

    return render_template(
        "dashboards/student.html",
        payments=payments
    )

# =========================
# 🚀 RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
