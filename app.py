from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "vistaoptica123"

# ---------------- DATABASE ----------------
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    return psycopg2.connect(DATABASE_URL)

def query(sql, params=(), fetchone=False, fetchall=False, commit=False):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, params)

    result = None
    if fetchone:
        result = cur.fetchone()
    if fetchall:
        result = cur.fetchall()

    if commit:
        db.commit()

    cur.close()
    db.close()
    return result

# ---------------- CREATE TABLES ----------------
def init_db():
    query("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT,
        password TEXT,
        role TEXT
    );
    """, commit=True)

    query("""
    CREATE TABLE IF NOT EXISTS patients(
        id SERIAL PRIMARY KEY,
        name TEXT,
        dni TEXT,
        phone TEXT
    );
    """, commit=True)

    query("""
    CREATE TABLE IF NOT EXISTS exams(
        id SERIAL PRIMARY KEY,
        patient_id INTEGER,
        od TEXT,
        oi TEXT,
        diagnosis TEXT,
        notes TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """, commit=True)

    query("""
    CREATE TABLE IF NOT EXISTS orders(
        id SERIAL PRIMARY KEY,
        patient_id INTEGER,
        frame TEXT,
        lens TEXT,
        status TEXT
    );
    """, commit=True)

    query("""
    CREATE TABLE IF NOT EXISTS payments(
        id SERIAL PRIMARY KEY,
        patient_id INTEGER,
        amount NUMERIC,
        concept TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """, commit=True)

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        u = query("SELECT * FROM users WHERE username=%s AND password=%s", (user,pwd), fetchone=True)

        if u:
            session["user"] = u[1]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    patients = query("SELECT COUNT(*) FROM patients", fetchone=True)[0]
    exams = query("SELECT COUNT(*) FROM exams", fetchone=True)[0]
    orders = query("SELECT COUNT(*) FROM orders", fetchone=True)[0]
    income = query("SELECT COALESCE(SUM(amount),0) FROM payments", fetchone=True)[0]

    return render_template("dashboard.html", patients=patients, exams=exams, orders=orders, income=income)

# ---------------- PATIENTS ----------------
@app.route("/patients", methods=["GET","POST"])
def patients():
    if request.method == "POST":
        query(
            "INSERT INTO patients (name,dni,phone) VALUES (%s,%s,%s)",
            (request.form["name"], request.form["dni"], request.form["phone"]),
            commit=True
        )

    data = query("SELECT * FROM patients", fetchall=True)
    return render_template("patients.html", patients=data)

# ---------------- EXAMS ----------------
@app.route("/exam/<int:pid>", methods=["GET","POST"])
def exam(pid):
    if request.method == "POST":
        query("""
            INSERT INTO exams (patient_id,od,oi,diagnosis,notes)
            VALUES (%s,%s,%s,%s,%s)
        """,(pid,request.form["od"],request.form["oi"],request.form["diagnosis"],request.form["notes"]), commit=True)

        return redirect("/dashboard")

    patient = query("SELECT * FROM patients WHERE id=%s",(pid,),fetchone=True)
    return render_template("exam.html", patient=patient)

# ---------------- ORDERS ----------------
@app.route("/orders", methods=["GET","POST"])
def orders():
    if request.method == "POST":
        query(
