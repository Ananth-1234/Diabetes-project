# ==========================================
# IMPORTS
# ==========================================
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from utils.db import get_db, init_db
from utils.prediction import predict_diabetes
from utils.gemini_ai import generate_recommendation, chat_with_ai

# ==========================================
# APP CONFIG
# ==========================================
app = Flask(__name__)
app.config.from_object(Config)

# ==========================================
# HOME
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")

# ==========================================
# REGISTER
# ==========================================
@app.route("/register", methods=["GET", "POST"])
def register():
    role = request.args.get("role") or request.form.get("role")

    if request.method == "POST":
        db = get_db()

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if role == "doctor":
            specialization = request.form["specialization"]
            experience = request.form["experience"]

            db.execute("""
                INSERT INTO doctors (name, email, password, specialization, experience)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, password, specialization, experience))

        elif role == "patient":
            age = request.form["age"]
            gender = request.form["gender"]

            db.execute("""
                INSERT INTO patients (name, email, password, age, gender)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, password, age, gender))

        db.commit()
        return redirect(url_for("login", role=role))

    return render_template("register.html", role=role)

# ==========================================
# LOGIN
# ==========================================
@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role") or request.form.get("role")

    if request.method == "POST":
        db = get_db()
        email = request.form["email"]
        password = request.form["password"]

        if role == "doctor":
            user = db.execute("SELECT * FROM doctors WHERE email=?", (email,)).fetchone()
        else:
            user = db.execute("SELECT * FROM patients WHERE email=?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = role

            if role == "doctor":
                return redirect(url_for("doctor_dashboard"))
            else:
                return redirect(url_for("patient_dashboard"))

    return render_template("login.html", role=role)

# ==========================================
# LOGOUT
# ==========================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ==========================================
# DOCTOR DASHBOARD
# ==========================================
@app.route("/doctor/dashboard")
def doctor_dashboard():
    db = get_db()
    doctor = db.execute("SELECT * FROM doctors WHERE id=?",
                        (session["user_id"],)).fetchone()
    return render_template("doctor/doctor_dashboard.html", doctor=doctor)

# ==========================================
# DOCTOR APPOINTMENTS
# ==========================================
@app.route("/doctor/appointments")
def doctor_appointments():
    db = get_db()
    appointments = db.execute("""
        SELECT appointments.*, patients.name AS patient_name
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        WHERE doctor_id=?
    """, (session["user_id"],)).fetchall()

    return render_template("doctor/doctor_appointments.html",
                           appointments=appointments)

# ==========================================
# UPDATE APPOINTMENT
# ==========================================
@app.route("/doctor/update/<int:id>/<action>")
def update_appointment(id, action):
    db = get_db()
    if action == "accept":
        db.execute("UPDATE appointments SET status='Accepted' WHERE id=?", (id,))
    elif action == "reject":
        db.execute("UPDATE appointments SET status='Rejected' WHERE id=?", (id,))
    db.commit()
    return redirect(url_for("doctor_appointments"))

# ==========================================
# COMPLETE APPOINTMENT
# ==========================================
@app.route("/doctor/complete/<int:id>")
def complete_appointment(id):
    db = get_db()
    db.execute("UPDATE appointments SET status='Completed' WHERE id=?", (id,))
    db.commit()
    return redirect(url_for("doctor_appointments"))

# ==========================================
# ADD NOTES
# ==========================================
@app.route("/doctor/notes/<int:id>", methods=["GET", "POST"])
def add_notes(id):
    db = get_db()

    if request.method == "POST":
        notes = request.form["notes"]
        db.execute("UPDATE appointments SET notes=? WHERE id=?", (notes, id))
        db.commit()
        return redirect(url_for("doctor_appointments"))

    appointment = db.execute("""
        SELECT appointments.*, patients.name AS patient_name
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        WHERE appointments.id=?
    """, (id,)).fetchone()

    return render_template("doctor/doctor_notes.html", appointment=appointment)

# ==========================================
# PATIENT DASHBOARD
# ==========================================
@app.route("/patient/dashboard")
def patient_dashboard():
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id=?",
                         (session["user_id"],)).fetchone()
    return render_template("patient/patient_dashboard.html", patient=patient)

# ==========================================
# PREDICTION PAGE
# ==========================================
@app.route("/patient/prediction")
def prediction_page():
    age = None
    # If a patient is logged in, fetch their age to prefill the form
    if session.get("user_id") and session.get("role") == "patient":
        db = get_db()
        patient = db.execute("SELECT age FROM patients WHERE id=?", (session["user_id"],)).fetchone()
        if patient:
            age = patient["age"]

    return render_template("patient/prediction.html", age=age)

# ==========================================
# PREDICT ROUTE
# ==========================================
@app.route("/predict", methods=["POST"])
def predict():
    pregnancies = float(request.form["pregnancies"])
    glucose = float(request.form["glucose"])
    blood_pressure = float(request.form["blood_pressure"])
    skin_thickness = float(request.form["skin_thickness"])
    insulin = float(request.form["insulin"])
    bmi = float(request.form["bmi"])
    dpf = float(request.form["dpf"])
    age = float(request.form["age"])

    result, probability = predict_diabetes(
        pregnancies, glucose, blood_pressure,
        skin_thickness, insulin, bmi,
        dpf, age
    )

    patient_data = f"""
    Glucose: {glucose}
    BMI: {bmi}
    Age: {age}
    """

    recommendation = generate_recommendation(patient_data, result)

    return render_template("patient/result.html",
                           result=result,
                           probability=probability,
                           recommendation=recommendation)

# ==========================================
# DOCTORS LIST
# ==========================================
@app.route("/patient/doctors")
def doctors_list():
    db = get_db()
    doctors = db.execute("SELECT * FROM doctors").fetchall()
    return render_template("patient/doctors_list.html", doctors=doctors)

# ==========================================
# BOOK APPOINTMENT
# ==========================================
@app.route("/patient/book/<int:doctor_id>", methods=["GET", "POST"])
def book_appointment(doctor_id):
    db = get_db()
    doctor = db.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()

    if request.method == "POST":
        date = request.form["date"]
        symptoms = request.form.get("symptoms", None)
        db.execute("""
            INSERT INTO appointments (patient_id, doctor_id, date, symptoms)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], doctor_id, date, symptoms))
        db.commit()
        return redirect(url_for("patient_appointments"))

    return render_template("patient/book_appointment.html", doctor=doctor)

# ==========================================
# PATIENT APPOINTMENTS
# ==========================================
@app.route("/patient/appointments")
def patient_appointments():
    db = get_db()
    appointments = db.execute("""
        SELECT appointments.*, doctors.name AS doctor_name
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE patient_id=?
    """, (session["user_id"],)).fetchall()

    return render_template("patient/patient_appointments.html",
                           appointments=appointments)

# ==========================================
# AI CHAT
# ==========================================
@app.route("/patient/ai_chat", methods=["GET", "POST"])
def ai_chat_page():
    response = None
    if request.method == "POST":
        message = request.form["message"]
        response = chat_with_ai(message)

    return render_template("patient/ai_chat.html", response=response)

# ==========================================
# RUN APP
# ==========================================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)