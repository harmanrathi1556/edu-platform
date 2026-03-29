from flask import Flask, render_template, request, redirect, session
from config import Config
from models import supabase
import bcrypt
import os

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# =========================
# 🏠 HOME ROUTE
# =========================
@app.route("/")
def home():
    return redirect("/login")

# =========================
# 🔐 LOGIN PAGE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        # Fetch user
        response = supabase.table("users").select("*").eq("email", email).execute()

        if response.data:
            user = response.data[0]

            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                
                if user["role"] != role:
                    return render_template("login.html", error="Role mismatch!")

                # Store session
                session["user_id"] = user["id"]
                session["role"] = user["role"]

                # Redirect based on role
                if role == "superadmin":
                    return redirect("/superadmin")
                elif role == "admin":
                    return redirect("/admin")
                elif role == "teacher":
                    return redirect("/teacher")
                else:
                    return redirect("/student")

        return render_template("login.html", error="Invalid credentials!")

    return render_template("login.html")

# =========================
# 👑 SUPER ADMIN DASHBOARD
# =========================
@app.route("/superadmin")
def superadmin():
    if "user_id" not in session or session.get("role") != "superadmin":
        return redirect("/login")

    # Fetch stats
    users = supabase.table("users").select("*").execute()
    institutes = supabase.table("institutes").select("*").execute()
    payments = supabase.table("payments").select("*").execute()

    total_users = len(users.data)
    total_institutes = len(institutes.data)
    total_revenue = sum([p["amount"] or 0 for p in payments.data]) if payments.data else 0

    return render_template(
        "dashboards/superadmin.html",
        total_users=total_users,
        total_institutes=total_institutes,
        total_revenue=total_revenue
    )

# =========================
# 🚀 REGISTER PAGE
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        institute_name = request.form.get("institute")

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create or get institute
        institute = supabase.table("institutes").select("*").eq("name", institute_name).execute()

        if institute.data:
            institute_id = institute.data[0]["id"]
        else:
            new_inst = supabase.table("institutes").insert({
                "name": institute_name
            }).execute()
            institute_id = new_inst.data[0]["id"]

        # Insert user
        supabase.table("users").insert({
            "name": name,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "role": role,
            "institute_id": institute_id
        }).execute()

        return redirect("/login")

    return render_template("register.html")

# =========================
# 🔓 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# 🚀 RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
