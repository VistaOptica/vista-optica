from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "vistaoptica123"

# ===============================
# DATABASE
# ===============================
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    return psycopg2.connect(DATABASE_URL)

# ===============================
# INIT DATABASE
# ===============================
def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            name TEXT,
            dni TEXT,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id),
            od TEXT,
            oi TEXT,
            diagnosis TEXT,
            notes TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id),
            frame TEXT,
            lens TEXT,
            status TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER REFERENCES patients(id),
            amount NUMERIC,
            concept TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    cur.close()
    db.close()

# ===============================
# CREATE DEFAULT ADMIN
# ===============================
def create_admin():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute(
            "INSERT INTO users (username,password,role) VALUES (%s,%s,%s)",
            ("admin", "1234", "admin")
        )
        db.commit()

    cur.close()
    db.close()

init_db()
create_admin()

# ===============================
# LOGIN
# ===============================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT username FROM users WHERE username=%s AND password=%s",
            (user,pwd)
        )
        u = cur.fetchone()

        cur.close()
        db.close()

        if u:
            session["user"] = user
            return redirect("/dashboard")

    return render_template("login.html")

# ===============================
# DASHBOARD
# ===============================
@app.route("/dashboard")
def dashboard():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM patients")
    patients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM exams")
    exams = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM payments")
    income = cur.fetchone()[0]

    cur.close()
    db.close()

    return render_template("dashboard.html", patients=patients, exams=exams, orders=orders, income=income)

# ===============================
# PATIENTS
# ===============================
@app.route("/patients", methods=["GET","POST"])
def patients():
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute(
            "INSERT INTO patients (name,dni,phone) VALUES (%s,%s,%s)",
            (request.form["name"],request.form["dni"],request.form["phone"])
        )
        db.commit()

    cur.execute("SELECT * FROM patients")
    data = cur.fetchall()

    cur.close()
    db.close()
    return render_template("patients.html", patients=data)

# ===============================
# EXAMS
# ===============================
@app.route("/exam/<int:pid>", methods=["GET","POST"])
def exam(pid):
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO exams (patient_id,od,oi,diagnosis,notes)
            VALUES (%s,%s,%s,%s,%s)
        """,(pid,
             request.form["od"],
             request.form["oi"],
             request.form["diagnosis"],
             request.form["notes"])
        )
        db.commit()
        return redirect("/dashboard")

    cur.execute("SELECT * FROM patients WHERE id=%s",(pid,))
    patient = cur.fetchone()

    cur.close()
    db.close()
    return render_template("exam.html", patient=patient)

# ===============================
# ORDERS
# ===============================
@app.route("/orders", methods=["GET","POST"])
def orders():
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO orders (patient_id,frame,lens,status)
            VALUES (%s,%s,%s,'En proceso')
        """,(request.form["patient"],request.form["frame"],request.form["lens"]))
        db.commit()

    cur.execute("""
        SELECT orders.*, patients.name
        FROM orders
        JOIN patients ON orders.patient_id = patients.id
    """)
    data = cur.fetchall()

    cur.close()
    db.close()
    return render_template("orders.html", orders=data)

# ===============================
# PAYMENTS
# ===============================
@app.route("/payments", methods=["GET","POST"])
def payments():
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO payments (patient_id,amount,concept)
            VALUES (%s,%s,%s)
        """,(request.form["patient"],request.form["amount"],request.form["concept"]))
        db.commit()

    cur.execute("""
        SELECT payments.*, patients.name
        FROM payments
        JOIN patients ON payments.patient_id = patients.id
    """)
    data = cur.fet
