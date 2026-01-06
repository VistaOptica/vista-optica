from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "vistaoptica123"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dni TEXT,
            phone TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            od TEXT,
            oi TEXT,
            diagnosis TEXT,
            notes TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            frame TEXT,
            lens TEXT,
            status TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            amount REAL,
            concept TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        db = get_db()
        u = db.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd)).fetchone()

        if u:
            session["user"] = u["username"]
            return redirect("/dashboard")
    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    db = get_db()
    patients = db.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    exams = db.execute("SELECT COUNT(*) FROM exams").fetchone()[0]
    orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    income = db.execute("SELECT SUM(amount) FROM payments").fetchone()[0]

    if income is None:
        income = 0

    return render_template("dashboard.html", patients=patients, exams=exams, orders=orders, income=income)

# ---------------- PATIENTS ----------------
@app.route("/patients", methods=["GET","POST"])
def patients():
    db = get_db()

    if request.method == "POST":
        name = request.form["name"]
        dni = request.form["dni"]
        phone = request.form["phone"]
        db.execute("INSERT INTO patients (name,dni,phone) VALUES (?,?,?)", (name,dni,phone))
        db.commit()

    data = db.execute("SELECT * FROM patients").fetchall()
    return render_template("patients.html", patients=data)

# ---------------- EXAMS ----------------
@app.route("/exam/<int:pid>", methods=["GET","POST"])
def exam(pid):
    db = get_db()

    if request.method == "POST":
        od = request.form["od"]
        oi = request.form["oi"]
        diagnosis = request.form["diagnosis"]
        notes = request.form["notes"]

        db.execute(
            "INSERT INTO exams (patient_id,od,oi,diagnosis,notes) VALUES (?,?,?,?,?)",
            (pid,od,oi,diagnosis,notes)
        )
        db.commit()

        return redirect("/dashboard")

    patient = db.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    return render_template("exam.html", patient=patient)

# ---------------- ORDERS ----------------
@app.route("/orders", methods=["GET","POST"])
def orders():
    db = get_db()

    if request.method == "POST":
        pid = request.form["patient"]
        frame = request.form["frame"]
        lens = request.form["lens"]
        status = "En proceso"

        db.execute(
            "INSERT INTO orders (patient_id,frame,lens,status) VALUES (?,?,?,?)",
            (pid,frame,lens,status)
        )
        db.commit()

    orders = db.execute("""
        SELECT orders.*, patients.name 
        FROM orders 
        JOIN patients ON orders.patient_id = patients.id
    """).fetchall()

    return render_template("orders.html", orders=orders)

# ---------------- PAYMENTS ----------------
@app.route("/payments", methods=["GET","POST"])
def payments():
    db = get_db()

    if request.method == "POST":
        pid = request.form["patient"]
        amount = request.form["amount"]
        concept = request.form["concept"]

        db.execute(
            "INSERT INTO payments (patient_id,amount,concept) VALUES (?,?,?)",
            (pid,amount,concept)
        )
        db.commit()

    data = db.execute("""
        SELECT payments.*, patients.name 
        FROM payments 
        JOIN patients ON payments.patient_id = patients.id
    """).fetchall()

    return render_template("payments.html", payments=data)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

